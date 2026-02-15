"""
data_hub.py - The Heart of the application
Holds all data, notifies observers of changes
"""

class DataHub:
    def __init__(self):
        self.samples = []
        self.columns = set()
        self.observers = []
        self.id_to_index = {}

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

        self._notify('samples_added', start_idx, len(new_samples))
        return len(new_samples)

    def update_rows(self, updated_samples):
        for i, sample in enumerate(updated_samples):
            if i < len(self.samples):
                self.samples[i] = sample
                self.columns.update(sample.keys())
        self._notify('samples_updated')

    def update_row(self, index, updates):
        if 0 <= index < len(self.samples):
            current = self.samples[index]
            for key, value in updates.items():
                if key in current:
                    current[key] = value
                else:
                    print(f"⚠️ Ignoring new column '{key}'")
            self._notify('row_updated', index)

    def delete_rows(self, indices):
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.samples):
                sample_id = self.samples[idx].get('Sample_ID')
                if sample_id in self.id_to_index:
                    del self.id_to_index[sample_id]
                del self.samples[idx]
        self._rebuild_columns()
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
