import time
import structlog
from typing import Dict

logger = structlog.get_logger()

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures: Dict[str, int] = {}
        self.last_failure_time: Dict[str, float] = {}
        self.state: Dict[str, str] = {}  # "CLOSED", "OPEN", "HALF_OPEN"
        # Admin overrides
        self.manual_override: Dict[str, bool] = {}  # True means forcibly closed (disabled)

    def is_open(self, supplier_code: str) -> bool:
        """Returns True if the circuit is open (supplier should be skipped)."""
        if self.manual_override.get(supplier_code, False):
            return True
            
        state = self.state.get(supplier_code, "CLOSED")
        
        if state == "CLOSED":
            return False
            
        if state == "OPEN":
            # Check if recovery timeout has passed
            last_fail = self.last_failure_time.get(supplier_code, 0)
            if time.time() - last_fail > self.recovery_timeout:
                # Transition to half-open
                self.state[supplier_code] = "HALF_OPEN"
                logger.info("circuit_breaker_half_open", supplier=supplier_code)
                return False
            return True
            
        # HALF_OPEN allows one request through
        if state == "HALF_OPEN":
            return False
            
        return False

    def record_success(self, supplier_code: str):
        """Record a successful request."""
        self.failures[supplier_code] = 0
        if self.state.get(supplier_code) in ["OPEN", "HALF_OPEN"]:
            self.state[supplier_code] = "CLOSED"
            logger.info("circuit_breaker_closed", supplier=supplier_code)

    def record_failure(self, supplier_code: str):
        """Record a failed request."""
        self.failures[supplier_code] = self.failures.get(supplier_code, 0) + 1
        self.last_failure_time[supplier_code] = time.time()
        
        state = self.state.get(supplier_code, "CLOSED")
        
        if state == "HALF_OPEN":
            self.state[supplier_code] = "OPEN"
            logger.warning("circuit_breaker_opened", supplier=supplier_code, reason="failed_in_half_open")
        elif state == "CLOSED" and self.failures[supplier_code] >= self.failure_threshold:
            self.state[supplier_code] = "OPEN"
            logger.warning("circuit_breaker_opened", supplier=supplier_code, reason="threshold_exceeded", failures=self.failures[supplier_code])

    def set_manual_override(self, supplier_code: str, disable: bool):
        """Manually disable or enable a supplier."""
        self.manual_override[supplier_code] = disable
        logger.info("circuit_breaker_manual_override", supplier=supplier_code, disabled=disable)

# Global singleton for V1
circuit_breaker = CircuitBreaker()
