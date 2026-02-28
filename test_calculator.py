import math

# Ensure attribute access for 'math' works even if module attribute resolution is unusual.
# Some tests patch 'calculator.math.pow', which requires 'math' to be accessible
# as an attribute on this module.
def __getattr__(name):
    if name == "math":
        return math
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class BusinessCalculator:

    @staticmethod
    def calculate_profit_margin(revenue, costs):
        if revenue == 0:
            return 0
        return ((revenue - costs) / revenue) * 100

    @staticmethod
    def calculate_roi(gain, cost):
        if cost == 0:
            return 0
        return ((gain - cost) / cost) * 100

    @staticmethod
    def calculate_compound_growth_rate(starting_value, ending_value, periods):
        if starting_value <= 0 or periods <= 0:
            return 0

        total_growth = (ending_value - starting_value) / starting_value
        return (total_growth / periods) * 100

    @staticmethod
    def calculate_break_even_point(fixed_costs, price_per_unit, variable_cost_per_unit):
        contribution_margin = price_per_unit - variable_cost_per_unit
        if contribution_margin <= 0:
            return None
        return fixed_costs / contribution_margin

    @staticmethod
    def calculate_discount_price(original_price, discount_percentage):
        discount_amount = original_price * (discount_percentage / 100)
        return original_price - discount_amount

    @staticmethod
    def calculate_tax_amount(amount, tax_rate):
        return amount * (tax_rate / 100)

    @staticmethod
    def calculate_net_present_value(cash_flows, discount_rate):
        npv = 0
        for period, cash_flow in enumerate(cash_flows):
            npv += cash_flow / math.pow(1 + discount_rate, period)
        return npv

    @staticmethod
    def calculate_markup_percentage(cost, selling_price):
        if cost == 0:
            return 0
        return ((selling_price - cost) / cost) * 100