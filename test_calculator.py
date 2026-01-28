import math
import pytest
from unittest.mock import patch

from calculator import BusinessCalculator


@pytest.fixture
def business_calculator():
    """Fixture to provide BusinessCalculator class for testing"""
    return BusinessCalculator


def test_businesscalculator_initialization(business_calculator):
    """Test that BusinessCalculator can be instantiated without errors"""
    instance = business_calculator()
    assert isinstance(instance, BusinessCalculator)


def test_businesscalculator_calculate_profit_margin_standard(business_calculator):
    """Test calculate_profit_margin with standard positive revenue and costs"""
    result = business_calculator.calculate_profit_margin(1000, 400)
    expected = ((1000 - 400) / 1000) * 100
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_profit_margin_zero_revenue(business_calculator):
    """Test calculate_profit_margin returns 0 when revenue is zero"""
    result = business_calculator.calculate_profit_margin(0, 400)
    assert result == 0


def test_businesscalculator_calculate_profit_margin_negative_profit(business_calculator):
    """Test calculate_profit_margin when costs exceed revenue (negative profit)"""
    result = business_calculator.calculate_profit_margin(500, 800)
    expected = ((500 - 800) / 500) * 100
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_roi_standard(business_calculator):
    """Test calculate_roi with standard positive gain and cost"""
    result = business_calculator.calculate_roi(1500, 1000)
    expected = ((1500 - 1000) / 1000) * 100
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_roi_zero_cost(business_calculator):
    """Test calculate_roi returns 0 when cost is zero"""
    result = business_calculator.calculate_roi(1500, 0)
    assert result == 0


def test_businesscalculator_calculate_roi_negative_gain(business_calculator):
    """Test calculate_roi with negative gain value"""
    result = business_calculator.calculate_roi(-500, 1000)
    expected = ((-500 - 1000) / 1000) * 100
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_compound_growth_rate_standard(business_calculator):
    """Test calculate_compound_growth_rate with valid positive values"""
    result = business_calculator.calculate_compound_growth_rate(1000, 2000, 2)
    total_growth = (2000 - 1000) / 1000
    expected = (total_growth / 2) * 100
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_compound_growth_rate_zero_starting_value(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when starting_value is zero"""
    result = business_calculator.calculate_compound_growth_rate(0, 2000, 2)
    assert result == 0


def test_businesscalculator_calculate_compound_growth_rate_negative_starting_value(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when starting_value is negative"""
    result = business_calculator.calculate_compound_growth_rate(-100, 200, 2)
    assert result == 0


def test_businesscalculator_calculate_compound_growth_rate_zero_periods(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when periods is zero"""
    result = business_calculator.calculate_compound_growth_rate(1000, 2000, 0)
    assert result == 0


def test_businesscalculator_calculate_compound_growth_rate_negative_periods(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when periods is negative"""
    result = business_calculator.calculate_compound_growth_rate(1000, 2000, -3)
    assert result == 0


def test_businesscalculator_calculate_compound_growth_rate_ending_less_than_start(business_calculator):
    """Test calculate_compound_growth_rate when ending_value is less than starting_value"""
    result = business_calculator.calculate_compound_growth_rate(2000, 1000, 2)
    total_growth = (1000 - 2000) / 2000
    expected = (total_growth / 2) * 100
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_break_even_point_standard(business_calculator):
    """Test calculate_break_even_point with valid positive margin"""
    result = business_calculator.calculate_break_even_point(1000, 50, 30)
    contribution_margin = 50 - 30
    expected = 1000 / contribution_margin
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_break_even_point_zero_contribution_margin(business_calculator):
    """Test calculate_break_even_point returns None when contribution margin is zero"""
    result = business_calculator.calculate_break_even_point(1000, 30, 30)
    assert result is None


def test_businesscalculator_calculate_break_even_point_negative_contribution_margin(business_calculator):
    """Test calculate_break_even_point returns None when contribution margin is negative"""
    result = business_calculator.calculate_break_even_point(1000, 20, 30)
    assert result is None


def test_businesscalculator_calculate_break_even_point_zero_fixed_costs(business_calculator):
    """Test calculate_break_even_point when fixed_costs is zero"""
    result = business_calculator.calculate_break_even_point(0, 50, 30)
    contribution_margin = 50 - 30
    expected = 0 / contribution_margin
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_discount_price_standard(business_calculator):
    """Test calculate_discount_price with standard values"""
    result = business_calculator.calculate_discount_price(100, 20)
    expected = 100 - (100 * (20 / 100))
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_discount_price_zero_discount(business_calculator):
    """Test calculate_discount_price with zero discount"""
    result = business_calculator.calculate_discount_price(100, 0)
    expected = 100
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_discount_price_over_100_discount(business_calculator):
    """Test calculate_discount_price with discount over 100%"""
    result = business_calculator.calculate_discount_price(100, 150)
    expected = 100 - (100 * (150 / 100))
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_tax_amount_standard(business_calculator):
    """Test calculate_tax_amount with standard positive tax rate"""
    result = business_calculator.calculate_tax_amount(200, 15)
    expected = 200 * (15 / 100)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_tax_amount_zero_tax_rate(business_calculator):
    """Test calculate_tax_amount with zero tax rate"""
    result = business_calculator.calculate_tax_amount(200, 0)
    expected = 0
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_tax_amount_negative_tax_rate(business_calculator):
    """Test calculate_tax_amount with negative tax rate"""
    result = business_calculator.calculate_tax_amount(200, -5)
    expected = 200 * (-5 / 100)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_net_present_value_standard(business_calculator):
    """Test calculate_net_present_value with multiple cash flows"""
    cash_flows = [100, 200, 300]
    discount_rate = 0.1
    expected = 0
    for period, cash_flow in enumerate(cash_flows):
        expected += cash_flow / math.pow(1 + discount_rate, period)
    result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_net_present_value_empty_cash_flows(business_calculator):
    """Test calculate_net_present_value with empty cash_flows list"""
    result = business_calculator.calculate_net_present_value([], 0.1)
    expected = 0
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_net_present_value_zero_discount_rate(business_calculator):
    """Test calculate_net_present_value with zero discount rate"""
    cash_flows = [100, 200, 300]
    discount_rate = 0.0
    expected = sum(cash_flows)
    result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_net_present_value_uses_math_pow(business_calculator):
    """Test calculate_net_present_value uses math.pow for discounting"""
    cash_flows = [100, 200]
    discount_rate = 0.1
    with patch("calculator.math.pow", wraps=math.pow) as mock_pow:
        result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)
        assert mock_pow.call_count == len(cash_flows)
        # basic sanity check that result is still correct
        expected = 0
        for period, cash_flow in enumerate(cash_flows):
            expected += cash_flow / math.pow(1 + discount_rate, period)
        assert result == pytest.approx(expected)


def test_businesscalculator_calculate_markup_percentage_standard(business_calculator):
    """Test calculate_markup_percentage with standard positive cost and selling price"""
    result = business_calculator.calculate_markup_percentage(100, 150)
    expected = ((150 - 100) / 100) * 100
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_markup_percentage_zero_cost(business_calculator):
    """Test calculate_markup_percentage returns 0 when cost is zero"""
    result = business_calculator.calculate_markup_percentage(0, 150)
    assert result == 0


def test_businesscalculator_calculate_markup_percentage_negative_markup(business_calculator):
    """Test calculate_markup_percentage when selling_price is less than cost"""
    result = business_calculator.calculate_markup_percentage(150, 100)
    expected = ((100 - 150) / 150) * 100
    assert result == pytest.approx(expected)


def test_businesscalculator_methods_do_not_raise_exceptions_with_negative_values(business_calculator):
    """Test methods handle negative inputs without raising exceptions"""
    # Profit margin with negative revenue and costs
    result_profit = business_calculator.calculate_profit_margin(-1000, -500)
    assert isinstance(result_profit, float)

    # ROI with negative cost
    result_roi = business_calculator.calculate_roi(500, -1000)
    assert isinstance(result_roi, float)

    # Discount price with negative discount
    result_discount = business_calculator.calculate_discount_price(100, -10)
    assert result_discount == pytest.approx(100 - (100 * (-10 / 100)))


def test_businesscalculator_calculate_net_present_value_exception_propagation(business_calculator):
    """Test calculate_net_present_value propagates exceptions from math.pow"""
    cash_flows = [100, 200]
    discount_rate = 0.1

    def side_effect(*args, **kwargs):
        raise OverflowError("test overflow")

    with patch("calculator.math.pow", side_effect=side_effect):
        with pytest.raises(OverflowError):
            business_calculator.calculate_net_present_value(cash_flows, discount_rate)