import math
import pytest
from unittest.mock import patch

from calculator import BusinessCalculator


@pytest.fixture
def business_calculator():
    """Fixture to create a BusinessCalculator instance."""
    return BusinessCalculator()


def test_businesscalculator_initialization(business_calculator):
    """Test BusinessCalculator can be instantiated (even though all methods are static)."""
    assert isinstance(business_calculator, BusinessCalculator)


def test_businesscalculator_calculate_profit_margin_normal(business_calculator):
    """Test calculate_profit_margin with typical positive revenue and costs."""
    revenue = 1000
    costs = 400
    expected = ((revenue - costs) / revenue) * 100
    result = business_calculator.calculate_profit_margin(revenue, costs)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_profit_margin_zero_revenue(business_calculator):
    """Test calculate_profit_margin returns 0 when revenue is zero."""
    result = business_calculator.calculate_profit_margin(0, 500)
    assert result == 0


def test_businesscalculator_calculate_profit_margin_negative_margin(business_calculator):
    """Test calculate_profit_margin when costs exceed revenue resulting in negative margin."""
    revenue = 500
    costs = 800
    expected = ((revenue - costs) / revenue) * 100
    result = business_calculator.calculate_profit_margin(revenue, costs)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_roi_normal(business_calculator):
    """Test calculate_roi with typical gain and cost."""
    gain = 1500
    cost = 1000
    expected = ((gain - cost) / cost) * 100
    result = business_calculator.calculate_roi(gain, cost)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_roi_zero_cost(business_calculator):
    """Test calculate_roi returns 0 when cost is zero."""
    result = business_calculator.calculate_roi(1000, 0)
    assert result == 0


def test_businesscalculator_calculate_roi_negative_roi(business_calculator):
    """Test calculate_roi when gain is less than cost resulting in negative ROI."""
    gain = 800
    cost = 1000
    expected = ((gain - cost) / cost) * 100
    result = business_calculator.calculate_roi(gain, cost)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_compound_growth_rate_normal(business_calculator):
    """Test calculate_compound_growth_rate with valid positive inputs."""
    start = 100
    end = 200
    periods = 2
    total_growth = (end - start) / start
    expected = (total_growth / periods) * 100
    result = business_calculator.calculate_compound_growth_rate(start, end, periods)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_compound_growth_rate_zero_starting_value(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when starting_value is zero."""
    result = business_calculator.calculate_compound_growth_rate(0, 200, 2)
    assert result == 0


def test_businesscalculator_calculate_compound_growth_rate_negative_starting_value(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when starting_value is negative."""
    result = business_calculator.calculate_compound_growth_rate(-100, 200, 2)
    assert result == 0


def test_businesscalculator_calculate_compound_growth_rate_zero_periods(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when periods is zero."""
    result = business_calculator.calculate_compound_growth_rate(100, 200, 0)
    assert result == 0


def test_businesscalculator_calculate_compound_growth_rate_negative_periods(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when periods is negative."""
    result = business_calculator.calculate_compound_growth_rate(100, 200, -1)
    assert result == 0


def test_businesscalculator_calculate_break_even_point_normal(business_calculator):
    """Test calculate_break_even_point with valid inputs and positive contribution margin."""
    fixed_costs = 1000
    price_per_unit = 50
    variable_cost_per_unit = 30
    contribution_margin = price_per_unit - variable_cost_per_unit
    expected = fixed_costs / contribution_margin
    result = business_calculator.calculate_break_even_point(
        fixed_costs, price_per_unit, variable_cost_per_unit
    )
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_break_even_point_zero_contribution_margin(business_calculator):
    """Test calculate_break_even_point returns None when contribution margin is zero."""
    result = business_calculator.calculate_break_even_point(
        1000, 50, 50
    )
    assert result is None


def test_businesscalculator_calculate_break_even_point_negative_contribution_margin(business_calculator):
    """Test calculate_break_even_point returns None when contribution margin is negative."""
    result = business_calculator.calculate_break_even_point(
        1000, 30, 50
    )
    assert result is None


def test_businesscalculator_calculate_break_even_point_zero_fixed_costs(business_calculator):
    """Test calculate_break_even_point with zero fixed costs returns 0.0 when margin positive."""
    result = business_calculator.calculate_break_even_point(
        0, 50, 30
    )
    assert result == pytest.approx(0.0)


def test_businesscalculator_calculate_discount_price_normal(business_calculator):
    """Test calculate_discount_price with typical original price and discount percentage."""
    original_price = 200
    discount_percentage = 10
    discount_amount = original_price * (discount_percentage / 100)
    expected = original_price - discount_amount
    result = business_calculator.calculate_discount_price(original_price, discount_percentage)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_discount_price_zero_discount(business_calculator):
    """Test calculate_discount_price when discount percentage is zero."""
    result = business_calculator.calculate_discount_price(200, 0)
    assert result == pytest.approx(200)


def test_businesscalculator_calculate_discount_price_hundred_percent_discount(business_calculator):
    """Test calculate_discount_price when discount percentage is 100."""
    result = business_calculator.calculate_discount_price(200, 100)
    assert result == pytest.approx(0)


def test_businesscalculator_calculate_tax_amount_normal(business_calculator):
    """Test calculate_tax_amount with typical amount and tax rate."""
    amount = 1000
    tax_rate = 15
    expected = amount * (tax_rate / 100)
    result = business_calculator.calculate_tax_amount(amount, tax_rate)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_tax_amount_zero_rate(business_calculator):
    """Test calculate_tax_amount when tax rate is zero."""
    result = business_calculator.calculate_tax_amount(1000, 0)
    assert result == pytest.approx(0)


def test_businesscalculator_calculate_tax_amount_negative_rate(business_calculator):
    """Test calculate_tax_amount when tax rate is negative (tax rebate scenario)."""
    amount = 1000
    tax_rate = -5
    expected = amount * (tax_rate / 100)
    result = business_calculator.calculate_tax_amount(amount, tax_rate)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_net_present_value_normal(business_calculator):
    """Test calculate_net_present_value with a list of positive and negative cash flows."""
    cash_flows = [-1000, 200, 300, 400, 500]
    discount_rate = 0.1
    expected = 0
    for period, cf in enumerate(cash_flows):
        expected += cf / math.pow(1 + discount_rate, period)
    result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_net_present_value_zero_discount_rate(business_calculator):
    """Test calculate_net_present_value when discount rate is zero (no discounting)."""
    cash_flows = [-1000, 300, 400]
    discount_rate = 0.0
    expected = sum(cash_flows)
    result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_net_present_value_empty_cash_flows(business_calculator):
    """Test calculate_net_present_value with empty cash_flows list returns 0."""
    result = business_calculator.calculate_net_present_value([], 0.1)
    assert result == pytest.approx(0)


def test_businesscalculator_calculate_net_present_value_uses_math_pow(business_calculator):
    """Test calculate_net_present_value uses math.pow with correct arguments."""
    cash_flows = [100, 200]
    discount_rate = 0.05
    with patch("math.pow", wraps=math.pow) as mock_pow:
        result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)
        assert result == pytest.approx(
            100 / math.pow(1 + discount_rate, 0) +
            200 / math.pow(1 + discount_rate, 1)
        )
        mock_pow.assert_any_call(1 + discount_rate, 0)
        mock_pow.assert_any_call(1 + discount_rate, 1)


def test_businesscalculator_calculate_markup_percentage_normal(business_calculator):
    """Test calculate_markup_percentage with typical cost and selling price."""
    cost = 100
    selling_price = 150
    expected = ((selling_price - cost) / cost) * 100
    result = business_calculator.calculate_markup_percentage(cost, selling_price)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_markup_percentage_zero_cost(business_calculator):
    """Test calculate_markup_percentage returns 0 when cost is zero."""
    result = business_calculator.calculate_markup_percentage(0, 150)
    assert result == 0


def test_businesscalculator_calculate_markup_percentage_negative_markup(business_calculator):
    """Test calculate_markup_percentage when selling price is less than cost (negative markup)."""
    cost = 150
    selling_price = 100
    expected = ((selling_price - cost) / cost) * 100
    result = business_calculator.calculate_markup_percentage(cost, selling_price)
    assert result == pytest.approx(expected)


def test_businesscalculator_methods_do_not_raise_unexpected_exceptions(business_calculator):
    """Test that methods handle edge numeric inputs without raising unexpected exceptions."""
    business_calculator.calculate_profit_margin(0, 0)
    business_calculator.calculate_roi(0, 0)
    business_calculator.calculate_compound_growth_rate(0, 0, 0)
    business_calculator.calculate_break_even_point(0, 0, 0)
    business_calculator.calculate_discount_price(0, 0)
    business_calculator.calculate_tax_amount(0, 0)
    business_calculator.calculate_net_present_value([0, 0], 0)
    business_calculator.calculate_markup_percentage(0, 0)