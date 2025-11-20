import math
import pytest
from unittest.mock import patch

from calculator import BusinessCalculator


@pytest.fixture
def bc_instance():
    """Create a BusinessCalculator instance for testing."""
    return BusinessCalculator()


def test_businesscalculator_initialization_instance_creation(bc_instance):
    """Test that BusinessCalculator can be instantiated."""
    assert isinstance(bc_instance, BusinessCalculator)


def test_businesscalculator_static_methods_callable_via_instance(bc_instance):
    """Test static methods are callable via instance and return correct result."""
    result = bc_instance.calculate_profit_margin(100, 50)
    assert result == 50.0


def test_businesscalculator_calculate_profit_margin_basic():
    """Test calculate_profit_margin with typical positive values."""
    result = BusinessCalculator.calculate_profit_margin(1000, 400)
    assert result == 60.0


def test_businesscalculator_calculate_profit_margin_zero_revenue():
    """Test calculate_profit_margin returns 0 when revenue is 0."""
    result = BusinessCalculator.calculate_profit_margin(0, 500)
    assert result == 0


def test_businesscalculator_calculate_profit_margin_cost_greater_than_revenue():
    """Test calculate_profit_margin returns negative margin when costs exceed revenue."""
    result = BusinessCalculator.calculate_profit_margin(100, 120)
    assert result == -20.0


def test_businesscalculator_calculate_roi_basic():
    """Test calculate_roi with typical positive values."""
    result = BusinessCalculator.calculate_roi(1200, 1000)
    assert result == 20.0


def test_businesscalculator_calculate_roi_zero_cost():
    """Test calculate_roi returns 0 when cost is 0."""
    result = BusinessCalculator.calculate_roi(500, 0)
    assert result == 0


def test_businesscalculator_calculate_roi_negative_gain():
    """Test calculate_roi with a negative ROI scenario."""
    result = BusinessCalculator.calculate_roi(800, 1000)
    assert result == -20.0


@pytest.mark.parametrize(
    "starting_value, ending_value, periods, expected",
    [
        (100, 200, 2, 50.0),     # 100% over 2 periods -> 50% per period
        (100, 50, 2, -25.0),     # -50% over 2 periods -> -25% per period
        (100, 100, 5, 0.0),      # No growth
    ],
)
def test_businesscalculator_calculate_compound_growth_rate_basic(starting_value, ending_value, periods, expected):
    """Test calculate_compound_growth_rate with various valid scenarios."""
    result = BusinessCalculator.calculate_compound_growth_rate(starting_value, ending_value, periods)
    assert result == pytest.approx(expected, rel=1e-9)


@pytest.mark.parametrize(
    "starting_value, ending_value, periods",
    [
        (0, 100, 3),          # starting_value <= 0
        (-10, 100, 3),        # starting_value <= 0
        (100, 200, 0),        # periods <= 0
        (100, 200, -2),       # periods <= 0
    ],
)
def test_businesscalculator_calculate_compound_growth_rate_invalid_inputs_return_zero(starting_value, ending_value, periods):
    """Test calculate_compound_growth_rate returns 0 for invalid inputs according to original behavior."""
    result = BusinessCalculator.calculate_compound_growth_rate(starting_value, ending_value, periods)
    assert result == 0


def test_businesscalculator_calculate_break_even_point_basic():
    """Test calculate_break_even_point with valid inputs."""
    result = BusinessCalculator.calculate_break_even_point(1000, 50, 30)
    assert result == 50.0


@pytest.mark.parametrize(
    "fixed_costs, price_per_unit, variable_cost_per_unit",
    [
        (1000, 20, 20),   # zero contribution margin
        (1000, 15, 20),   # negative contribution margin
    ],
)
def test_businesscalculator_calculate_break_even_point_no_solution_returns_none(fixed_costs, price_per_unit, variable_cost_per_unit):
    """Test calculate_break_even_point returns None when contribution margin <= 0."""
    result = BusinessCalculator.calculate_break_even_point(fixed_costs, price_per_unit, variable_cost_per_unit)
    assert result is None


def test_businesscalculator_calculate_discount_price_basic():
    """Test calculate_discount_price with a standard percentage discount."""
    result = BusinessCalculator.calculate_discount_price(100, 20)
    assert result == 80.0


def test_businesscalculator_calculate_discount_price_negative_discount_increases_price():
    """Test calculate_discount_price with a negative discount (i.e., markup)."""
    result = BusinessCalculator.calculate_discount_price(100, -10)
    assert result == 110.0


def test_businesscalculator_calculate_discount_price_over_100_produces_negative_price():
    """Test calculate_discount_price where discount exceeds 100%."""
    result = BusinessCalculator.calculate_discount_price(100, 150)
    assert result == -50.0


def test_businesscalculator_calculate_tax_amount_basic():
    """Test calculate_tax_amount with a positive tax rate."""
    result = BusinessCalculator.calculate_tax_amount(100, 7.5)
    assert result == 7.5


def test_businesscalculator_calculate_tax_amount_negative_rate():
    """Test calculate_tax_amount with a negative tax rate (rebate scenario)."""
    result = BusinessCalculator.calculate_tax_amount(100, -5)
    assert result == -5.0


def test_businesscalculator_calculate_tax_amount_zero_amount():
    """Test calculate_tax_amount with zero amount."""
    result = BusinessCalculator.calculate_tax_amount(0, 10)
    assert result == 0.0


def test_businesscalculator_calculate_net_present_value_basic_and_pow_calls():
    """Test calculate_net_present_value correct result and that math.pow is called per period."""
    cash_flows = [-1000, 400, 400, 400]
    discount_rate = 0.10

    # Compute expected using the real math.pow
    expected = sum(cf / math.pow(1 + discount_rate, t) for t, cf in enumerate(cash_flows))

    with patch("calculator.math.pow", side_effect=math.pow) as mock_pow:
        result = BusinessCalculator.calculate_net_present_value(cash_flows, discount_rate)
        assert result == pytest.approx(expected, rel=1e-9)
        assert mock_pow.call_count == len(cash_flows)
        # Validate the arguments used in calls
        for idx, call in enumerate(mock_pow.call_args_list):
            args, _ = call
            assert args[0] == pytest.approx(1 + discount_rate, rel=1e-12)
            assert args[1] == idx


def test_businesscalculator_calculate_net_present_value_zero_division_error():
    """Test calculate_net_present_value raises ZeroDivisionError when discount_rate = -1 leads to division by zero."""
    cash_flows = [1000, 100]
    with pytest.raises(ZeroDivisionError):
        BusinessCalculator.calculate_net_present_value(cash_flows, -1.0)


def test_businesscalculator_calculate_markup_percentage_basic():
    """Test calculate_markup_percentage with typical values."""
    result = BusinessCalculator.calculate_markup_percentage(80, 100)
    assert result == 25.0


def test_businesscalculator_calculate_markup_percentage_cost_zero_returns_zero():
    """Test calculate_markup_percentage returns 0 when cost is 0."""
    result = BusinessCalculator.calculate_markup_percentage(0, 100)
    assert result == 0.0


def test_businesscalculator_methods_callable_as_class_methods_and_instance_methods(bc_instance):
    """Test that all methods are callable both from class and instance consistently."""
    # Profit margin
    assert BusinessCalculator.calculate_profit_margin(200, 50) == pytest.approx(
        bc_instance.calculate_profit_margin(200, 50), rel=1e-12
    )
    # ROI
    assert BusinessCalculator.calculate_roi(150, 100) == pytest.approx(
        bc_instance.calculate_roi(150, 100), rel=1e-12
    )
    # Compound growth rate
    assert BusinessCalculator.calculate_compound_growth_rate(100, 150, 2) == pytest.approx(
        bc_instance.calculate_compound_growth_rate(100, 150, 2), rel=1e-12
    )
    # Break-even
    assert BusinessCalculator.calculate_break_even_point(500, 25, 20) == pytest.approx(
        bc_instance.calculate_break_even_point(500, 25, 20), rel=1e-12
    )
    # Discount price
    assert BusinessCalculator.calculate_discount_price(250, 10) == pytest.approx(
        bc_instance.calculate_discount_price(250, 10), rel=1e-12
    )
    # Tax amount
    assert BusinessCalculator.calculate_tax_amount(250, 8) == pytest.approx(
        bc_instance.calculate_tax_amount(250, 8), rel=1e-12
    )
    # Net present value
    flows = [-500, 200, 200, 200]
    rate = 0.05
    assert BusinessCalculator.calculate_net_present_value(flows, rate) == pytest.approx(
        bc_instance.calculate_net_present_value(flows, rate), rel=1e-12
    )
    # Markup percentage
    assert BusinessCalculator.calculate_markup_percentage(50, 65) == pytest.approx(
        bc_instance.calculate_markup_percentage(50, 65), rel=1e-12
    )