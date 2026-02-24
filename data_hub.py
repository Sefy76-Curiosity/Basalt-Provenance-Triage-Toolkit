"""
data_hub.py - The Heart of the application
Holds all data, notifies observers of changes
"""

from datetime import datetime

class DataHub:
    def __init__(self):
        self.samples = []
        self.columns = set()
        self.observers = []
        # Add these for auto-save tracking
        self._unsaved_changes = False
        self._last_change_time = None   # time of last unsaved change
        self._change_count = 0
        self.id_to_index = {}
        self._column_order = []

    def mark_unsaved(self):
        """Mark that there are unsaved changes"""
        self._unsaved_changes = True
        self._change_count += 1
        self._last_change_time = datetime.now()  # time of most recent change

    def mark_saved(self):
        """Mark that changes have been saved"""
        self._unsaved_changes = False
        self._change_count = 0

    def has_unsaved_changes(self):
        """Check if there are unsaved changes"""
        return self._unsaved_changes

    def add_samples(self, new_samples):
        """Add samples - keep column names as-is (already normalized)"""
        if not new_samples:
            return 0

        start_idx = len(self.samples)

        for sample in new_samples:
            # Ensure Sample_ID
            if 'Sample_ID' not in sample:
                sample['Sample_ID'] = f"SAMPLE_{len(self.samples)+1:04d}"

            self.id_to_index[sample['Sample_ID']] = len(self.samples)
            self.samples.append(sample)
            self.columns.update(sample.keys())

        self.mark_unsaved()
        self._notify('samples_added', start_idx, len(new_samples))
        return len(new_samples)

    def update_rows(self, updated_samples):
        """Bulk-replace samples by position while keeping id_to_index consistent."""
        for i, sample in enumerate(updated_samples):
            if i < len(self.samples):
                old_id = self.samples[i].get('Sample_ID')
                if old_id and old_id in self.id_to_index:
                    del self.id_to_index[old_id]
                self.samples[i] = sample
                self.columns.update(sample.keys())
                new_id = sample.get('Sample_ID')
                if new_id is not None:
                    self.id_to_index[new_id] = i
        self.mark_unsaved()
        self._notify('samples_updated')

    def update_row(self, index, updates):
        """Update a row with new values, adding new columns if needed"""
        if 0 <= index < len(self.samples):
            for key in updates.keys():
                if key not in self.columns:
                    self.columns.add(key)
                    print(f"📝 Added new column: {key}")
            self.samples[index].update(updates)
            self.mark_unsaved()
            self._notify('update', index)
            print(f"✅ Updated row {index} with: {list(updates.keys())}")
        else:
            print(f"❌ Index {index} out of range (max: {len(self.samples)-1})")

    def delete_rows(self, indices):
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.samples):
                sample_id = self.samples[idx].get('Sample_ID')
                if sample_id in self.id_to_index:
                    del self.id_to_index[sample_id]
                del self.samples[idx]
        self._rebuild_columns()
        self._rebuild_index()   # re-number remaining rows after deletions shift positions
        self.mark_unsaved()
        self._notify('samples_deleted', len(indices))

    def get_all(self):
        return self.samples

    def get_page(self, page, page_size=50):
        start = page * page_size
        end = start + page_size
        return self.samples[start:end]

    def get_by_id(self, sample_id):
        idx = self.id_to_index.get(sample_id)
        return self.samples[idx] if idx is not None else None

    def get_selected(self, indices):
        return [self.samples[i] for i in indices if 0 <= i < len(self.samples)]

    def row_count(self):
        return len(self.samples)

    def get_column_names(self):
        return sorted(list(self.columns))

    def register_observer(self, observer):
        self.observers.append(observer)

    def _notify(self, event, *args):
        for observer in self.observers:
            if hasattr(observer, 'on_data_changed'):
                try:
                    observer.on_data_changed(event, *args)
                except Exception as e:
                    print(f"Observer error: {e}")

    def _rebuild_columns(self):
        self.columns.clear()
        for sample in self.samples:
            self.columns.update(sample.keys())

    def _rebuild_index(self):
        """Rebuild id_to_index from scratch — needed after deletions shift row positions."""
        self.id_to_index = {
            sample['Sample_ID']: i
            for i, sample in enumerate(self.samples)
            if 'Sample_ID' in sample
        }

    def clear_all(self):
        """Clear all samples and reset state"""
        self.samples = []
        self.columns = set()
        self.id_to_index = {}
        self._column_order = []
        self.mark_unsaved()
        self._notify('samples_cleared')

    @property
    def column_order(self):
        """Get column order (auto-generates if not set)"""
        if not self._column_order:
            self._column_order = sorted(self.columns)
        return self._column_order

    @column_order.setter
    def column_order(self, order):
        """Set column order"""
        self._column_order = order

    def notify_all_observers(self, event, *args):
        """Public method to notify all observers of a data change"""
        self._notify(event, *args)
