import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { NormalizedOffer } from './api/inventoryApi';

/** Offer selected for quote builder, tagged with the search that produced it. */
export type SelectedOffer = NormalizedOffer & {
  search_request_id: string;
};

interface QuoteState {
  selectedOffers: SelectedOffer[];
  /** Last successful search id — used when adding offers from results. */
  lastSearchRequestId: string | null;
}

const initialState: QuoteState = {
  selectedOffers: [],
  lastSearchRequestId: null,
};

const quoteSlice = createSlice({
  name: 'quote',
  initialState,
  reducers: {
    setLastSearchRequestId: (state, action: PayloadAction<string>) => {
      state.lastSearchRequestId = action.payload;
    },
    addOffer: (state, action: PayloadAction<SelectedOffer>) => {
      // Enforce one product type per quote (V1 rule)
      const currentType = state.selectedOffers[0]?.type;
      if (currentType && currentType !== action.payload.type) {
        state.selectedOffers = [];
      }

      if (!state.selectedOffers.find((o) => o.id === action.payload.id)) {
        state.selectedOffers.push(action.payload);
      }
    },
    removeOffer: (state, action: PayloadAction<string>) => {
      state.selectedOffers = state.selectedOffers.filter((o) => o.id !== action.payload);
    },
    clearOffers: (state) => {
      state.selectedOffers = [];
    },
  },
});

export const { addOffer, removeOffer, clearOffers, setLastSearchRequestId } = quoteSlice.actions;
export default quoteSlice.reducer;
