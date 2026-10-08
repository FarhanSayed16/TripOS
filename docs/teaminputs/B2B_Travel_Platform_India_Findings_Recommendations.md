**B2B Travel Platform\
India Operational, Ownership & Compliance Review**

*Findings and recommendations based on the attached B2B Travel Platform
workflow*

# 1. Executive Summary

The existing workflow covers the core B2B travel journey well: agency
registration, profile setup, CRM, search and booking, pricing/markup,
invoicing, email, booking management, roles and phased development.
However, before production launch in India, additional controls are
needed around KYC/agency verification, customer consent and privacy,
tax/invoicing, payments and refunds, supplier terms, cancellation
disclosures, auditability, information security, grievance handling and
ownership of operational decisions.

The recommendations below are intended as a product/operations control
framework and not as a substitute for an India-qualified lawyer, tax
advisor or privacy counsel. Applicable laws and contractual requirements
should be validated before launch.

# 2. Key Gaps / Missed Areas

  --------------------------------------------------------------------------
  Gap                      Finding / Risk            Priority
  ------------------------ ------------------------- -----------------------
  Agency KYC & onboarding  Registration captures     High
                           agency details, but there 
                           is no explicit KYC/KYB    
                           verification workflow,    
                           document status,          
                           approval/rejection,       
                           periodic review or        
                           suspension process.       

  GST & tax controls       GST details are captured, High
                           but tax treatment,        
                           invoice numbering         
                           controls, tax breakup,    
                           place-of-supply logic,    
                           credit/debit notes and    
                           reconciliation controls   
                           are not defined.          

  Customer consent &       CRM stores contact,       High
  privacy                  traveller and booking     
                           information, but consent, 
                           privacy notice, purpose   
                           limitation,               
                           retention/deletion and    
                           data-subject request      
                           handling are not defined. 

  Payment compliance       Payment is part of the    High
                           flow, but payment-gateway 
                           ownership, settlement,    
                           failed-payment handling,  
                           chargebacks, wallet       
                           controls and segregation  
                           of duties are not         
                           defined.                  

  Refund & cancellation    Refund/cancellation       High
  governance               status exists, but        
                           approval rules, supplier  
                           refund dependency,        
                           timelines, customer       
                           communication and refund  
                           reconciliation are not    
                           defined.                  

  Supplier/airline/hotel   The workflow does not     High
  terms                    require                   
                           acceptance/display of     
                           supplier fare rules,      
                           cancellation terms,       
                           baggage/fare conditions   
                           and service restrictions  
                           before booking.           

  Audit trail              Activity timeline is      High
                           mentioned, but immutable  
                           audit events, user        
                           identity, timestamp,      
                           old/new values and admin  
                           actions are not           
                           explicitly required.      

  Access/security controls Roles are defined, but    High
                           MFA, password policy,     
                           session controls,         
                           privileged access,        
                           API-key protection,       
                           encryption, breach        
                           response and periodic     
                           access review are         
                           missing.                  

  Grievance/dispute        There is no defined       Medium
  handling                 customer/agent complaint  
                           workflow, escalation      
                           matrix, SLA, evidence     
                           repository or closure     
                           tracking.                 

  Contract/document        Supplier agreements,      High
  management               agency agreements,        
                           platform terms and        
                           version acceptance are    
                           not represented in the    
                           workflow.                 

  Communication compliance Email infrastructure is   Medium
                           covered, but              
                           consent/preferences,      
                           transactional vs          
                           promotional communication 
                           and                       
                           unsubscribe/preference    
                           management are not        
                           defined.                  

  Business continuity      No explicit backup,       Medium
                           disaster recovery,        
                           supplier outage           
                           procedure, incident       
                           management or business    
                           continuity ownership is   
                           defined.                  

  Fraud/risk controls      No explicit suspicious    High
                           booking/payment           
                           detection, velocity       
                           limits, duplicate booking 
                           checks, high-risk agency  
                           controls or manual review 
                           queue is defined.         

  Operational              Supplier cost/customer    High
  reconciliation           receipt/markup are        
                           listed, but daily         
                           reconciliation, exception 
                           handling and              
                           maker-checker controls    
                           are not defined.          

  Data ownership           Ownership of              High
                           agency/customer/booking   
                           data, retention periods,  
                           exports and deletion      
                           responsibilities is not   
                           explicitly allocated.     
  --------------------------------------------------------------------------

# 3. Recommended Ownership Model

  -----------------------------------------------------------------------
  Owner                               Primary accountability
  ----------------------------------- -----------------------------------
  Platform Product Owner              Owns product requirements, policy
                                      configuration, workflow design,
                                      acceptance criteria and
                                      cross-functional sign-off.

  Operations / Business Operations    Owns day-to-day booking operations,
                                      supplier exceptions,
                                      cancellation/refund operations,
                                      service SLAs and escalation
                                      management.

  Finance / Tax                       Owns GST/tax configuration, invoice
                                      controls, credit/debit notes,
                                      payment settlement,
                                      wallet/reconciliation and financial
                                      audit readiness.

  Legal / Compliance                  Owns agency/platform agreements,
                                      terms, privacy notice, consent
                                      wording, supplier contractual
                                      controls, regulatory interpretation
                                      and legal escalation.

  Information Security / Technology   Owns authentication, access
                                      control, encryption, API security,
                                      logging, backups, vulnerability
                                      management, incident response and
                                      DR.

  Data Protection / Privacy Owner     Owns privacy-by-design, data
                                      inventory, retention/deletion
                                      rules, consent records and handling
                                      of privacy/data requests.

  Supplier / Contracting Team         Owns supplier onboarding,
                                      contracts, commercial terms, SLA,
                                      inventory/fare-rule accuracy and
                                      supplier compliance.

  Customer Support / Grievance Owner  Owns complaints, customer
                                      communications, escalation,
                                      evidence and closure within defined
                                      SLAs.

  Agency / Sales Team                 Owns agency onboarding information,
                                      commercial relationship, agent
                                      training and first-level business
                                      escalations.

  Internal Audit / Risk               Performs periodic control testing,
                                      access reviews, reconciliation
                                      checks and exception reporting.
  -----------------------------------------------------------------------

# 4. India-Focused Compliance Controls to Add

**Agency onboarding:** Capture legal entity/agency name, business
address, responsible person, GST details where applicable, supporting
documents, verification status, approver, date of verification and
suspension/review status.

**Terms & acceptance:** Maintain versioned platform terms, agency terms,
privacy notice and booking/cancellation terms. Record who accepted,
when, IP/device information where appropriate, and the version accepted.

**Privacy & personal data:** Build privacy-by-design into CRM and
booking flows: identify data collected, purpose, access rights,
retention period, deletion/anonymisation process, vendor access and
incident escalation. Obtain appropriate consent/notices where required.

**GST/invoicing:** Define the tax owner and rules for invoice
generation, tax breakup, GSTIN validation, invoice numbering,
credit/debit notes, cancellations/refunds and accounting reconciliation.

**Payments:** Use approved payment partners/processors as appropriate.
Keep payment credentials/tokenisation out of the application where
possible; define settlement, failed payment, chargeback and refund
ownership.

**Travel disclosures:** Before final booking, clearly display
supplier/fare rules, baggage, cancellation/change conditions,
non-refundable elements, convenience/markup/other fees and total payable
amount.

**Refunds:** Create a maker-checker or approval mechanism for manual
refunds, with reason codes, supplier reference, approved amount,
evidence, payment status and customer notification.

**Security:** Implement MFA for privileged users, least-privilege RBAC,
strong authentication, secrets/API-key protection, encryption in
transit/at rest, security logging and periodic access reviews.

**Incident response:** Define severity levels, responsible owners,
escalation contacts, containment steps, evidence preservation and
legal/privacy notification assessment.

**Retention:** Create a data retention schedule for agency, customer,
traveller, booking, invoice, payment and communication records; automate
archival/deletion where legally and operationally appropriate.

**Grievance management:** Provide a visible support/grievance channel,
ticket ID, SLA, escalation hierarchy, evidence and closure reason.

**Vendor management:** Maintain a register of suppliers, processors and
technology vendors, with contracts, data access, security requirements,
SLA and termination/offboarding controls.

# 5. Workflow Enhancements

**Registration → KYC/KYB → Approval:** Do not activate booking
privileges until required agency verification is complete.

**Customer creation → Privacy/consent controls:** Show the applicable
privacy notice and capture required consent/preferences before
collecting or using personal data.

**Search → Fare/Terms display → Revalidation:** Show important fare
rules and total price before payment; revalidate immediately before
booking.

**Payment → Supplier booking:** Use a controlled payment status machine:
initiated → authorised/paid → booking requested → confirmed/failed →
refund/chargeback if applicable.

**Booking confirmation → Invoice → Communication:** Generate the correct
tax/commercial document and retain the communication event and document
version.

**Cancellation → Supplier response → Refund approval → Payment →
Closure:** Track each stage separately rather than using one generic
refund status.

**Admin action → Audit log:** Log privileged changes, pricing overrides,
refunds, user/role changes, configuration changes and API/integration
changes.

**Exception → Escalation → Resolution:** Every operational exception
should have an owner, SLA, reason code and closure evidence.

# 6. Suggested RACI for Critical Processes

  --------------------------------------------------------------------------------------------
  Process              Responsible            Accountable    Consulted          Informed
  -------------------- ---------------------- -------------- ------------------ --------------
  Agency KYC approval  Operations /           Platform       Legal/Compliance   Sales
                       Compliance                                               

  GST/invoice          Finance/Tax            Platform       Legal/Tax          Operations
  configuration                                                                 

  Booking failure      Operations             Technology     Supplier Team      Customer
                                                                                Support

  Manual refund        Finance/Operations     Platform       Compliance for     Customer
                                                             exceptions         Support

  Customer complaint   Customer Support       Operations     Legal for disputes Sales

  Security incident    Technology/Security    Platform       Legal/Privacy      Operations

  Supplier contract    Supplier/Contracting   Operations     Legal              Finance

  Data                 Privacy/Data Owner     Technology     Legal              Operations
  retention/deletion                                                            

  Access review        Security/IT            Platform       Compliance         Department
                                                                                Heads
  --------------------------------------------------------------------------------------------

# 7. Recommended Development Priority

**P0 -- Before production:** KYC/KYB, RBAC/MFA for privileged users,
audit logs, privacy/terms acceptance, fare-rule disclosure,
payment/refund state management, GST/invoice controls, supplier
contracts, grievance/escalation and security/incident controls.

**P1 -- Early production:** Automated reconciliation, retention/deletion
automation, fraud/risk rules, access review dashboards, supplier SLA
monitoring, backup/DR testing and advanced reporting.

**P2 -- Scale:** AI-assisted support/operations, anomaly detection,
predictive fraud/risk, automated supplier exception handling and
advanced analytics---subject to governance and privacy controls.

# 8. Ownership Matrix to Embed in the Product

  -------------------------------------------------------------------------------
  Object / Process  Business Owner        Control Owner         Key Control
  ----------------- --------------------- --------------------- -----------------
  Customer data     Agency/Platform       Privacy/Data Owner    Access,
                    relationship owner                          retention,
                                                                deletion, export

  Traveller data    Agency/booking owner  Privacy/Data Owner    Purpose, access,
                                                                retention,
                                                                supplier sharing

  Booking           Operations            Platform Product      Status, supplier
                                          Owner                 reference, audit
                                                                trail

  Price/markup      Business/Commercial   Finance               Approval and
                                                                override logs

  Invoice/GST       Finance/Tax           Finance Head          Numbering, tax
                                                                logic,
                                                                credit/debit
                                                                notes

  Payment           Finance               Technology/Security   Settlement,
                                                                refund,
                                                                chargeback
                                                                controls

  Supplier content  Supplier Team         Operations            Fare rules,
                                                                availability, SLA

  Refund            Operations/Finance    Finance               Approval,
                                                                evidence,
                                                                reconciliation

  User access       Department owner      Security/IT           Least privilege,
                                                                periodic review

  Legal terms       Legal/Compliance      Legal/Compliance      Version control
                                                                and acceptance
                                                                evidence
  -------------------------------------------------------------------------------

# 9. Important Legal/Compliance Note

This document identifies product and operational controls that should be
considered for an India-market B2B travel platform. It does not
constitute legal advice or certify compliance. Before production launch,
the company should have India-qualified legal counsel and a tax/GST
professional validate the final terms, privacy framework, data
processing arrangements, invoicing/tax treatment, payment structure,
supplier contracts and grievance process against the platform\'s actual
business model.

# 10. Source Basis

The attached source workflow currently covers agency
registration/profile, dashboard, CRM, search and booking,
pricing/markup, branded invoices, email, booking management, roles,
operational sequence and phased development. For example, it specifies
agency GST/registration details and invoice settings, and it already
includes supplier cost, customer receipt, markup, taxes, refunds and
wallet in the finance sequence. fileciteturn0file0L4-L9 It also
defines roles and the development phases for payments, refunds,
reconciliation, permissions and audit logs.
fileciteturn0file0L34-L47
