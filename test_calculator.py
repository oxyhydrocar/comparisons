import math
import pytest
from unittest.mock import patch, call
from calculator import BusinessCalculator


@pytest.fixture
def calculator():
    """Create BusinessCalculator instance for testing"""
    return BusinessCalculator()


def test_businesscalculator_initialization():
    """Test that BusinessCalculator can be instantiated"""
    calc = BusinessCalculator()
    assert isinstance(calc, BusinessCalculator)


def test_businesscalculator_calculate_profit_margin_basic(calculator):
    """Test calculate_profit_margin with typical positive numbers"""
    result = calculator.calculate_profit_margin(revenue=200, costs=150)
    assert result == pytest.approx(25.0)


def test_businesscalculator_calculate_profit_margin_zero_revenue(calculator):
    """Test calculate_profit_margin returns 0 when revenue is zero"""
    result = calculator.calculate_profit_margin(revenue=0, costs=100)
    assert result == 0


def test_businesscalculator_calculate_profit_margin_negative_cost(calculator):
    """Test calculate_profit_margin with negative costs (e.g., rebates)"""
    result = calculator.calculate_profit_margin(revenue=100, costs=-20)
    assert result == pytest.approx(120.0)


def test_businesscalculator_calculate_roi_basic(calculator):
    """Test calculate_roi with typical gain and cost"""
    result = calculator.calculate_roi(gain=150, cost=100)
    assert result == pytest.approx(50.0)


def test_businesscalculator_calculate_roi_zero_cost(calculator):
    """Test calculate_roi returns 0 when cost is zero"""
    result = calculator.calculate_roi(gain=150, cost=0)
    assert result == 0


def test_businesscalculator_calculate_compound_growth_rate_basic(calculator):
    """Test calculate_compound_growth_rate average periodic percentage growth"""
    result = calculator.calculate_compound_growth_rate(starting_value=100, ending_value=200, periods=2)
    # total_growth = (200-100)/100 = 1.0; per-period % = 1.0/2 * 100 = 50%
    assert result == pytest.approx(50.0)


def test_businesscalculator_calculate_compound_growth_rate_invalid_inputs(calculator):
    """Test calculate_compound_growth_rate returns 0 for non-positive starting value or periods"""
    assert calculator.calculate_compound_growth_rate(starting_value=0, ending_value=200, periods=2) == 0
    assert calculator.calculate_compound_growth_rate(starting_value=100, ending_value=200, periods=0) == 0
    assert calculator.calculate_compound_growth_rate(starting_value=-10, ending_value=200, periods=2) == 0
    assert calculator.calculate_compound_growth_rate(starting_value=100, ending_value=200, periods=-1) == 0


def test_businesscalculator_calculate_break_even_point_basic(calculator):
    """Test calculate_break_even_point with valid contribution margin"""
    result = calculator.calculate_break_even_point(fixed_costs=1000, price_per_unit=50, variable_cost_per_unit=30)
    assert result == pytest.approx(50.0)


def test_businesscalculator_calculate_break_even_point_no_solution(calculator):
    """Test calculate_break_even_point returns None when contribution margin is non-positive"""
    assert calculator.calculate_break_even_point(fixed_costs=1000, price_per_unit=30, variable_cost_per_unit=30) is None
    assert calculator.calculate_break_even_point(fixed_costs=1000, price_per_unit=25, variable_cost_per_unit=30) is None


def test_businesscalculator_calculate_discount_price_basic(calculator):
    """Test calculate_discount_price with typical discount percentage"""
    result = calculator.calculate_discount_price(original_price=100, discount_percentage=20)
    assert result == pytest.approx(80.0)


def test_businesscalculator_calculate_discount_price_edge_rates(calculator):
    """Test calculate_discount_price with 0% and 100% discounts"""
    assert calculator.calculate_discount_price(original_price=100, discount_percentage=0) == pytest.approx(100.0)
    assert calculator.calculate_discount_price(original_price=100, discount_percentage=100) == pytest.approx(0.0)


def test_businesscalculator_calculate_tax_amount_basic(calculator):
    """Test calculate_tax_amount computes percentage-based tax"""
    result = calculator.calculate_tax_amount(amount=200, tax_rate=10)
    assert result == pytest.approx(20.0)


def test_businesscalculator_calculate_net_present_value_basic(calculator):
    """Test calculate_net_present_value with standard cash flows and discount rate"""
    cash_flows = [-1000, 500, 500, 500]
    r = 0.1
    expected = sum(cf / ((1 + r) ** t) for t, cf in enumerate(cash_flows))
    result = calculator.calculate_net_present_value(cash_flows=cash_flows, discount_rate=r)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_net_present_value_zero_discount_rate(calculator):
    """Test calculate_net_present_value when discount rate is zero equals sum of cash flows"""
    cash_flows = [100, -50, 25]
    result = calculator.calculate_net_present_value(cash_flows=cash_flows, discount_rate=0)
    assert result == sum(cash_flows)


def test_businesscalculator_calculate_net_present_value_empty_list(calculator):
    """Test calculate_net_present_value with empty cash flows list returns 0"""
    result = calculator.calculate_net_present_value(cash_flows=[], discount_rate=0.1)
    assert result == 0


def test_businesscalculator_calculate_net_present_value_negative_discount_rate(calculator):
    """Test calculate_net_present_value with a negative discount rate (> -1)"""
    cash_flows = [100, 100]
    r = -0.5
    expected = sum(cf / ((1 + r) ** t) for t, cf in enumerate(cash_flows))
    result = calculator.calculate_net_present_value(cash_flows=cash_flows, discount_rate=r)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_net_present_value_rate_minus_one_raises(calculator):
    """Test calculate_net_present_value raises ZeroDivisionError when discount rate is -1 and t>=1 exists"""
    cash_flows = [100, 100]  # period 1 denominator becomes 0
    with pytest.raises(ZeroDivisionError):
        calculator.calculate_net_present_value(cash_flows=cash_flows, discount_rate=-1.0)


def test_businesscalculator_calculate_markup_percentage_basic(calculator):
    """Test calculate_markup_percentage with standard inputs"""
    result = calculator.calculate_markup_percentage(cost=80, selling_price=100)
    assert result == pytest.approx(25.0)


def test_businesscalculator_calculate_markup_percentage_zero_cost(calculator):
    """Test calculate_markup_percentage returns 0 when cost is zero"""
    result = calculator.calculate_markup_percentage(cost=0, selling_price=100)
    assert result == 0


def test_businesscalculator_calculate_net_present_value_uses_math_pow(calculator):
    """Test calculate_net_present_value uses math.pow for discounting"""
    cash_flows = [100, 200, 300]
    r = 0.1
    base = 1 + r

    with patch('calculator.math.pow', side_effect=math.pow) as mock_pow:
        result = calculator.calculate_net_present_value(cash_flows=cash_flows, discount_rate=r)

    # Verify calls for periods 0, 1, 2
    expected_calls = [call(base, 0), call(base, 1), call(base, 2)]
    mock_pow.assert_has_calls(expected_calls, any_order=False)

    # Ensure result is still correct with patched pow
    expected = sum(cf / (base ** t) for t, cf in enumerate(cash_flows))
    assert result == pytest.approx(expected)