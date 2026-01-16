import math
import pytest
from unittest.mock import patch

from calculator import BusinessCalculator


@pytest.fixture
def business_calculator():
    """Fixture to create a BusinessCalculator instance for testing."""
    return BusinessCalculator()


def test_business_calculator_initialization(business_calculator):
    """Test that BusinessCalculator can be instantiated."""
    assert isinstance(business_calculator, BusinessCalculator)


def test_business_calculator_calculate_profit_margin_normal(business_calculator):
    """Test calculate_profit_margin with normal positive revenue and costs."""
    result = business_calculator.calculate_profit_margin(1000, 400)
    expected = ((1000 - 400) / 1000) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_profit_margin_zero_revenue(business_calculator):
    """Test calculate_profit_margin returns 0 when revenue is zero."""
    result = business_calculator.calculate_profit_margin(0, 400)
    assert result == 0


def test_business_calculator_calculate_profit_margin_negative_profit(business_calculator):
    """Test calculate_profit_margin when costs exceed revenue (negative margin)."""
    result = business_calculator.calculate_profit_margin(500, 800)
    expected = ((500 - 800) / 500) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_profit_margin_negative_revenue(business_calculator):
    """Test calculate_profit_margin with negative revenue (as implemented)."""
    result = business_calculator.calculate_profit_margin(-1000, 400)
    expected = ((-1000 - 400) / -1000) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_roi_normal(business_calculator):
    """Test calculate_roi with normal positive gain and cost."""
    result = business_calculator.calculate_roi(1500, 1000)
    expected = ((1500 - 1000) / 1000) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_roi_zero_cost(business_calculator):
    """Test calculate_roi returns 0 when cost is zero."""
    result = business_calculator.calculate_roi(1500, 0)
    assert result == 0


def test_business_calculator_calculate_roi_negative_gain(business_calculator):
    """Test calculate_roi with negative gain (loss scenario)."""
    result = business_calculator.calculate_roi(500, 1000)
    expected = ((500 - 1000) / 1000) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_compound_growth_rate_normal(business_calculator):
    """Test calculate_compound_growth_rate with valid positive values."""
    result = business_calculator.calculate_compound_growth_rate(1000, 2000, 4)
    total_growth = (2000 - 1000) / 1000
    expected = (total_growth / 4) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_compound_growth_rate_zero_starting_value(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when starting_value is zero."""
    result = business_calculator.calculate_compound_growth_rate(0, 2000, 4)
    assert result == 0


def test_business_calculator_calculate_compound_growth_rate_negative_starting_value(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when starting_value is negative."""
    result = business_calculator.calculate_compound_growth_rate(-1000, 2000, 4)
    assert result == 0


def test_business_calculator_calculate_compound_growth_rate_zero_periods(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when periods is zero."""
    result = business_calculator.calculate_compound_growth_rate(1000, 2000, 0)
    assert result == 0


def test_business_calculator_calculate_compound_growth_rate_negative_periods(business_calculator):
    """Test calculate_compound_growth_rate returns 0 when periods is negative."""
    result = business_calculator.calculate_compound_growth_rate(1000, 2000, -2)
    assert result == 0


def test_business_calculator_calculate_compound_growth_rate_decreasing_value(business_calculator):
    """Test calculate_compound_growth_rate when ending_value is less than starting_value."""
    result = business_calculator.calculate_compound_growth_rate(2000, 1000, 4)
    total_growth = (1000 - 2000) / 2000
    expected = (total_growth / 4) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_break_even_point_normal(business_calculator):
    """Test calculate_break_even_point with valid positive contribution margin."""
    result = business_calculator.calculate_break_even_point(10000, 50, 30)
    contribution_margin = 50 - 30
    expected = 10000 / contribution_margin
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_break_even_point_zero_contribution_margin(business_calculator):
    """Test calculate_break_even_point returns None when contribution margin is zero."""
    result = business_calculator.calculate_break_even_point(10000, 30, 30)
    assert result is None


def test_business_calculator_calculate_break_even_point_negative_contribution_margin(business_calculator):
    """Test calculate_break_even_point returns None when contribution margin is negative."""
    result = business_calculator.calculate_break_even_point(10000, 20, 30)
    assert result is None


def test_business_calculator_calculate_break_even_point_zero_fixed_costs(business_calculator):
    """Test calculate_break_even_point with zero fixed costs."""
    result = business_calculator.calculate_break_even_point(0, 50, 30)
    contribution_margin = 50 - 30
    expected = 0 / contribution_margin
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_discount_price_normal(business_calculator):
    """Test calculate_discount_price with normal positive discount."""
    result = business_calculator.calculate_discount_price(200, 10)
    expected = 200 - (200 * (10 / 100))
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_discount_price_zero_discount(business_calculator):
    """Test calculate_discount_price with zero discount percentage."""
    result = business_calculator.calculate_discount_price(200, 0)
    expected = 200
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_discount_price_full_discount(business_calculator):
    """Test calculate_discount_price with 100 percent discount."""
    result = business_calculator.calculate_discount_price(200, 100)
    expected = 0
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_discount_price_negative_discount(business_calculator):
    """Test calculate_discount_price with negative discount percentage (price increase)."""
    result = business_calculator.calculate_discount_price(200, -10)
    expected = 200 - (200 * (-10 / 100))
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_tax_amount_normal(business_calculator):
    """Test calculate_tax_amount with normal positive tax rate."""
    result = business_calculator.calculate_tax_amount(1000, 15)
    expected = 1000 * (15 / 100)
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_tax_amount_zero_tax_rate(business_calculator):
    """Test calculate_tax_amount with zero tax rate."""
    result = business_calculator.calculate_tax_amount(1000, 0)
    expected = 0
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_tax_amount_negative_tax_rate(business_calculator):
    """Test calculate_tax_amount with negative tax rate (rebate scenario)."""
    result = business_calculator.calculate_tax_amount(1000, -5)
    expected = 1000 * (-5 / 100)
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_normal(business_calculator):
    """Test calculate_net_present_value with typical cash flows and discount rate."""
    cash_flows = [1000, 2000, 3000]
    discount_rate = 0.1
    result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)

    expected = 0
    for period, cash_flow in enumerate(cash_flows):
        expected += cash_flow / math.pow(1 + discount_rate, period)

    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_zero_discount_rate(business_calculator):
    """Test calculate_net_present_value with zero discount rate."""
    cash_flows = [1000, 2000, 3000]
    discount_rate = 0
    result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)

    expected = sum(cash_flows)
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_empty_cash_flows(business_calculator):
    """Test calculate_net_present_value with empty cash flows list."""
    cash_flows = []
    discount_rate = 0.1
    result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)
    expected = 0
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_negative_discount_rate(business_calculator):
    """Test calculate_net_present_value with negative discount rate (as implemented)."""
    cash_flows = [1000, 2000, 3000]
    discount_rate = -0.05
    result = business_calculator.calculate_net_present_value(cash_flows, discount_rate)

    expected = 0
    for period, cash_flow in enumerate(cash_flows):
        expected += cash_flow / math.pow(1 + discount_rate, period)

    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_uses_math_pow(business_calculator):
    """Test calculate_net_present_value uses math.pow for discounting."""
    cash_flows = [1000, 2000]
    discount_rate = 0.1
    with patch("calculator.math.pow") as mock_pow:
        mock_pow.side_effect = math.pow
        business_calculator.calculate_net_present_value(cash_flows, discount_rate)
        assert mock_pow.call_count == len(cash_flows)


def test_business_calculator_calculate_net_present_value_math_pow_exception(business_calculator):
    """Test calculate_net_present_value propagates exceptions from math.pow."""
    cash_flows = [1000]
    discount_rate = 0.1

    def raise_error(*args, **kwargs):
        raise ValueError("math.pow error")

    with patch("calculator.math.pow", side_effect=raise_error):
        with pytest.raises(ValueError):
            business_calculator.calculate_net_present_value(cash_flows, discount_rate)


def test_business_calculator_calculate_markup_percentage_normal(business_calculator):
    """Test calculate_markup_percentage with normal positive cost and selling price."""
    result = business_calculator.calculate_markup_percentage(100, 150)
    expected = ((150 - 100) / 100) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_markup_percentage_zero_cost(business_calculator):
    """Test calculate_markup_percentage returns 0 when cost is zero."""
    result = business_calculator.calculate_markup_percentage(0, 150)
    assert result == 0


def test_business_calculator_calculate_markup_percentage_negative_markup(business_calculator):
    """Test calculate_markup_percentage when selling price is less than cost."""
    result = business_calculator.calculate_markup_percentage(150, 100)
    expected = ((100 - 150) / 150) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_markup_percentage_negative_cost(business_calculator):
    """Test calculate_markup_percentage with negative cost (as implemented)."""
    result = business_calculator.calculate_markup_percentage(-100, 150)
    expected = ((150 - -100) / -100) * 100
    assert result == pytest.approx(expected)