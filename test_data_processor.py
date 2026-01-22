from utils import v
import threading


class SalesRecord:
    def __init__(self, record_id, product, amount, date, region):
        # Support both 'record_id' and 'id' attribute names to satisfy all tests
        self.record_id = record_id
        self.id = record_id
        self.product = product
        self.amount = amount
        self.date = date
        self.region = region

    def to_dict(self):
        return {
            "record_id": self.record_id,
            "product": self.product,
            "amount": self.amount,
            "date": self.date,
            "region": self.region,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            record_id=v(data, "record_id", "i"),
            product=v(data, "product", "s"),
            amount=v(data, "amount", "f"),
            date=v(data, "date", "s"),
            region=v(data, "region", "s"),
        )


class DataProcessor:
    def __init__(self, records):
        self.records = records

    def sort_by_amount(self):
        sorted_records = self.records.copy()
        n = len(sorted_records)

        for i in range(n):
            for j in range(0, n - i - 1):
                if sorted_records[j].amount > sorted_records[j + 1].amount:
                    sorted_records[j], sorted_records[j + 1] = (
                        sorted_records[j + 1],
                        sorted_records[j],
                    )

        return sorted_records

    def filter_by_region(self, region):
        return [record for record in self.records if record.region == region]

    def filter_by_product(self, product):
        return [record for record in self.records if record.product == product]

    def get_total_sales(self):
        return sum(record.amount for record in self.records)

    def get_average_sale(self):
        if not self.records:
            return 0.0
        return self.get_total_sales() / len(self.records)

    def group_by_region(self):
        grouped = {}
        for record in self.records:
            if record.region not in grouped:
                grouped[record.region] = []
            grouped[record.region].append(record)
        return grouped

    def get_top_products(self, limit=5):
        product_sales = {}
        for record in self.records:
            if record.product not in product_sales:
                product_sales[record.product] = 0
            product_sales[record.product] += record.amount

        sorted_products = sorted(
            product_sales.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_products[:limit]

    def process_records_parallel(self, threshold):
        results = []
        lock = threading.Lock()

        def process_chunk(chunk):
            local_results = []
            for record in chunk:
                if record.amount > threshold:
                    local_results.append(record)
            if local_results:
                with lock:
                    results.extend(local_results)

        if not self.records:
            return []

        chunk_size = len(self.records) // 4 if len(self.records) >= 4 else 1
        threads = []

        for i in range(0, len(self.records), chunk_size):
            chunk = self.records[i : i + chunk_size]
            thread = threading.Thread(target=process_chunk, args=(chunk,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return results