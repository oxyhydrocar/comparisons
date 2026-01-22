import math
import pytest
from unittest.mock import patch

from calculator import BusinessCalculator


@pytest.fixture
def business_calculator():
    """Fixture to create a BusinessCalculator instance"""
    return BusinessCalculator()


def test_business_calculator_initialization(business_calculator):
    """Test BusinessCalculator can be instantiated"""
    assert isinstance(business_calculator, BusinessCalculator)


def test_business_calculator_calculate_profit_margin_normal_case(business_calculator):
    """Test calculate_profit_margin with normal positive revenue and costs"""
    revenue = 1000
    costs = 400
    result = business_calculator.calculate_profit_margin(revenue, costs)
    expected = ((revenue - costs) / revenue) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_profit_margin_zero_revenue(business_calculator):
    """Test calculate_profit_margin returns 0 when revenue is zero"""
    result = business_calculator.calculate_profit_margin(0, 500)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_profit_margin_negative_profit(business_calculator):
    """Test calculate_profit_margin with costs greater than revenue (negative profit margin)"""
    revenue = 500
    costs = 800
    result = business_calculator.calculate_profit_margin(revenue, costs)
    expected = ((revenue - costs) / revenue) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_profit_margin_negative_revenue(business_calculator):
    """Test calculate_profit_margin with negative revenue"""
    revenue = -1000
    costs = 400
    result = business_calculator.calculate_profit_margin(revenue, costs)
    expected = ((revenue - costs) / revenue) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_roi_normal_case(business_calculator):
    """Test calculate_roi with normal positive gain and cost"""
    gain = 1500
    cost = 1000
    result = business_calculator.calculate_roi(gain, cost)
    expected = ((gain - cost) / cost) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_roi_zero_cost(business_calculator):
    """Test calculate_roi returns 0 when cost is zero"""
    result = business_calculator.calculate_roi(1000, 0)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_roi_negative_roi(business_calculator):
    """Test calculate_roi with gain less than cost (negative ROI)"""
    gain = 800
    cost = 1000
    result = business_calculator.calculate_roi(gain, cost)
    expected = ((gain - cost) / cost) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_compound_growth_rate_normal_case(business_calculator):
    """Test calculate_compound_growth_rate with normal positive values"""
    starting_value = 1000
    ending_value = 2000
    periods = 4
    result = business_calculator.calculate_compound_growth_rate(
        starting_value, ending_value, periods
    )
    total_growth = (ending_value - starting_value) / starting_value
    expected = (total_growth / periods) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_compound_growth_rate_zero_starting_value(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when starting_value is zero"""
    result = business_calculator.calculate_compound_growth_rate(0, 2000, 4)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_compound_growth_rate_negative_starting_value(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when starting_value is negative"""
    result = business_calculator.calculate_compound_growth_rate(-1000, 2000, 4)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_compound_growth_rate_zero_periods(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when periods is zero"""
    result = business_calculator.calculate_compound_growth_rate(1000, 2000, 0)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_compound_growth_rate_negative_periods(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when periods is negative"""
    result = business_calculator.calculate_compound_growth_rate(1000, 2000, -3)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_compound_growth_rate_ending_less_than_start(business_calculator):
    """Test calculate_compound_growth_rate when ending_value is less than starting_value (negative growth)"""
    starting_value = 2000
    ending_value = 1000
    periods = 4
    result = business_calculator.calculate_compound_growth_rate(
        starting_value, ending_value, periods
    )
    total_growth = (ending_value - starting_value) / starting_value
    expected = (total_growth / periods) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_break_even_point_normal_case(business_calculator):
    """Test calculate_break_even_point with normal positive values"""
    fixed_costs = 10000
    price_per_unit = 50
    variable_cost_per_unit = 30
    result = business_calculator.calculate_break_even_point(
        fixed_costs, price_per_unit, variable_cost_per_unit
    )
    contribution_margin = price_per_unit - variable_cost_per_unit
    expected = fixed_costs / contribution_margin
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_break_even_point_zero_contribution_margin(business_calculator):
    """Test calculate_break_even_point returns None when contribution margin is zero"""
    result = business_calculator.calculate_break_even_point(
        10000, 50, 50
    )
    assert result is None


def test_business_calculator_calculate_break_even_point_negative_contribution_margin(business_calculator):
    """Test calculate_break_even_point returns None when contribution margin is negative"""
    result = business_calculator.calculate_break_even_point(
        10000, 30, 50
    )
    assert result is None


def test_business_calculator_calculate_break_even_point_zero_fixed_costs(business_calculator):
    """Test calculate_break_even_point with zero fixed costs"""
    result = business_calculator.calculate_break_even_point(
        0, 50, 30
    )
    expected = 0 / (50 - 30)
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_discount_price_normal_case(business_calculator):
    """Test calculate_discount_price with normal values"""
    original_price = 200
    discount_percentage = 25
    result = business_calculator.calculate_discount_price(
        original_price, discount_percentage
    )
    discount_amount = original_price * (discount_percentage / 100)
    expected = original_price - discount_amount
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_discount_price_zero_discount(business_calculator):
    """Test calculate_discount_price with zero discount"""
    result = business_calculator.calculate_discount_price(200, 0)
    assert result == pytest.approx(200)


def test_business_calculator_calculate_discount_price_full_discount(business_calculator):
    """Test calculate_discount_price with 100 percent discount"""
    result = business_calculator.calculate_discount_price(200, 100)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_discount_price_negative_discount(business_calculator):
    """Test calculate_discount_price with negative discount percentage"""
    result = business_calculator.calculate_discount_price(200, -10)
    discount_amount = 200 * (-10 / 100)
    expected = 200 - discount_amount
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_tax_amount_normal_case(business_calculator):
    """Test calculate_tax_amount with normal values"""
    amount = 1000
    tax_rate = 20
    result = business_calculator.calculate_tax_amount(amount, tax_rate)
    expected = amount * (tax_rate / 100)
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_tax_amount_zero_tax_rate(business_calculator):
    """Test calculate_tax_amount with zero tax rate"""
    result = business_calculator.calculate_tax_amount(1000, 0)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_tax_amount_negative_tax_rate(business_calculator):
    """Test calculate_tax_amount with negative tax rate"""
    amount = 1000
    tax_rate = -5
    result = business_calculator.calculate_tax_amount(amount, tax_rate)
    expected = amount * (tax_rate / 100)
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_normal_case(business_calculator):
    """Test calculate_net_present_value with a list of cash flows and positive discount rate"""
    cash_flows = [1000, 2000, 3000]
    discount_rate = 0.1
    result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)
    expected = sum(
        cf / ((1 + discount_rate) ** period)
        for period, cf in enumerate(cash_flows)
    )
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_zero_discount_rate(business_calculator):
    """Test calculate_net_present_value with zero discount rate"""
    cash_flows = [1000, 2000, 3000]
    discount_rate = 0
    result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)
    expected = sum(
        cf / ((1 + discount_rate) ** period)
        for period, cf in enumerate(cash_flows)
    )
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_empty_cash_flows(business_calculator):
    """Test calculate_net_present_value with empty cash flows list"""
    result = business_calculator.calculate_net_present_value([], 0.1)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_net_present_value_negative_discount_rate(business_calculator):
    """Test calculate_net_present_value with negative discount rate"""
    cash_flows = [1000, 2000, 3000]
    discount_rate = -0.05
    result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)
    expected = sum(
        cf / ((1 + discount_rate) ** period)
        for period, cf in enumerate(cash_flows)
    )
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_uses_math_pow(business_calculator):
    """Test calculate_net_present_value uses math.pow for discounting"""
    cash_flows = [1000, 2000]
    discount_rate = 0.1
    with patch("math.pow", wraps=math.pow) as mock_pow:
        result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)
        expected = sum(
            cf / math.pow(1 + discount_rate, period)
            for period, cf in enumerate(cash_flows)
        )
        assert result == pytest.approx(expected)
        assert mock_pow.call_count == len(cash_flows)


def test_business_calculator_calculate_net_present_value_invalid_cash_flows_raises_type_error(business_calculator):
    """Test calculate_net_present_value raises TypeError for non-iterable cash_flows"""
    with pytest.raises(TypeError):
        business_calculator.calculate_net_present_value(None, 0.1)


def test_business_calculator_calculate_markup_percentage_normal_case(business_calculator):
    """Test calculate_markup_percentage with normal cost and selling_price"""
    cost = 100
    selling_price = 150
    result = business_calculator.calculate_markup_percentage(cost, selling_price)
    expected = ((selling_price - cost) / cost) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_markup_percentage_zero_cost(business_calculator):
    """Test calculate_markup_percentage returns 0 when cost is zero"""
    result = business_calculator.calculate_markup_percentage(0, 150)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_markup_percentage_negative_markup(business_calculator):
    """Test calculate_markup_percentage with selling_price less than cost (negative markup)"""
    cost = 150
    selling_price = 100
    result = business_calculator.calculate_markup_percentage(cost, selling_price)
    expected = ((selling_price - cost) / cost) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_markup_percentage_negative_cost(business_calculator):
    """Test calculate_markup_percentage with negative cost"""
    cost = -100
    selling_price = 150
    result = business_calculator.calculate_markup_percentage(cost, selling_price)
    expected = ((selling_price - cost) / cost) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_methods_raise_type_error_on_invalid_types(business_calculator):
    """Test that methods raise TypeError when provided with invalid argument types"""
    with pytest.raises(TypeError):
        business_calculator.calculate_profit_margin("invalid", 100)
    with pytest.raises(TypeError):
        business_calculator.calculate_roi(100, "invalid")
    with pytest.raises(TypeError):
        business_calculator.calculate_compound_growth_rate("start", "end", "periods")
    with pytest.raises(TypeError):
        business_calculator.calculate_break_even_point("fixed", "price", "variable")
    with pytest.raises(TypeError):
        business_calculator.calculate_discount_price("price", "discount")
    with pytest.raises(TypeError):
        business_calculator.calculate_tax_amount("amount", "rate")
    with pytest.raises(TypeError):
        business_calculator.calculate_markup_percentage("cost", "selling")