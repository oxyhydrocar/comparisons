import math
import pytest
from unittest.mock import patch
from calculator import BusinessCalculator


@pytest.fixture
def calc():
    """Create a BusinessCalculator instance for testing."""
    return BusinessCalculator()


def test_businesscalculator_initialization(calc):
    """Test BusinessCalculator can be instantiated."""
    assert isinstance(calc, BusinessCalculator)
    assert hasattr(calc, "calculate_profit_margin")


def test_businesscalculator_calculate_profit_margin_basic(calc):
    """Test calculate_profit_margin returns correct percentage for normal case."""
    result = calc.calculate_profit_margin(1000, 400)
    assert result == pytest.approx(60.0)


def test_businesscalculator_calculate_profit_margin_zero_revenue(calc):
    """Test calculate_profit_margin returns 0 when revenue is zero to avoid division by zero."""
    result = calc.calculate_profit_margin(0, 400)
    assert result == 0


def test_businesscalculator_calculate_profit_margin_negative_margin(calc):
    """Test calculate_profit_margin handles negative margin when costs exceed revenue."""
    result = calc.calculate_profit_margin(100, 150)
    assert result == pytest.approx(-50.0)


def test_businesscalculator_calculate_roi_basic(calc):
    """Test calculate_roi returns correct percentage for normal case."""
    result = calc.calculate_roi(1200, 1000)
    assert result == pytest.approx(20.0)


def test_businesscalculator_calculate_roi_cost_zero_returns_zero(calc):
    """Test calculate_roi returns 0 when cost is zero to avoid division by zero."""
    result = calc.calculate_roi(1200, 0)
    assert result == 0


def test_businesscalculator_calculate_roi_negative(calc):
    """Test calculate_roi handles negative ROI when gain is less than cost."""
    result = calc.calculate_roi(500, 1000)
    assert result == pytest.approx(-50.0)


def test_businesscalculator_calculate_compound_growth_rate_basic(calc):
    """Test calculate_compound_growth_rate returns average growth per period as percentage."""
    result = calc.calculate_compound_growth_rate(100, 200, 4)
    assert result == pytest.approx(25.0)


@pytest.mark.parametrize(
    "starting_value, ending_value, periods, expected",
    [
        (0, 200, 4, 0),
        (-100, 200, 4, 0),
        (100, 200, 0, 0),
        (100, 200, -2, 0),
    ],
)
def test_businesscalculator_calculate_compound_growth_rate_invalid_inputs(calc, starting_value, ending_value, periods, expected):
    """Test calculate_compound_growth_rate returns 0 for non-positive starting_value or periods."""
    result = calc.calculate_compound_growth_rate(starting_value, ending_value, periods)
    assert result == expected


def test_businesscalculator_calculate_compound_growth_rate_negative_growth(calc):
    """Test calculate_compound_growth_rate handles negative growth when ending value is less than starting value."""
    result = calc.calculate_compound_growth_rate(200, 100, 2)
    assert result == pytest.approx(-25.0)


def test_businesscalculator_calculate_break_even_point_basic(calc):
    """Test calculate_break_even_point returns correct units for normal case."""
    result = calc.calculate_break_even_point(1000, 50, 30)
    assert result == pytest.approx(50.0)


@pytest.mark.parametrize(
    "fixed_costs, price, variable_cost, expected",
    [
        (1000, 30, 30, None),  # zero contribution margin
        (1000, 25, 30, None),  # negative contribution margin
    ],
)
def test_businesscalculator_calculate_break_even_point_no_contribution_margin_returns_none(calc, fixed_costs, price, variable_cost, expected):
    """Test calculate_break_even_point returns None when contribution margin is not positive."""
    result = calc.calculate_break_even_point(fixed_costs, price, variable_cost)
    assert result is expected


def test_businesscalculator_calculate_break_even_point_negative_fixed_costs(calc):
    """Test calculate_break_even_point handles negative fixed costs (e.g., net subsidies)."""
    result = calc.calculate_break_even_point(-1000, 50, 30)
    assert result == pytest.approx(-50.0)


def test_businesscalculator_calculate_discount_price_basic(calc):
    """Test calculate_discount_price returns correct discounted price."""
    result = calc.calculate_discount_price(100, 10)
    assert result == pytest.approx(90.0)


def test_businesscalculator_calculate_discount_price_edge_discounts(calc):
    """Test calculate_discount_price handles zero, negative, and over-100% discounts."""
    assert calc.calculate_discount_price(100, 0) == pytest.approx(100.0)
    assert calc.calculate_discount_price(100, -10) == pytest.approx(110.0)
    assert calc.calculate_discount_price(100, 150) == pytest.approx(-50.0)


def test_businesscalculator_calculate_tax_amount_basic(calc):
    """Test calculate_tax_amount returns correct tax amount."""
    result = calc.calculate_tax_amount(100, 7.5)
    assert result == pytest.approx(7.5)


def test_businesscalculator_calculate_tax_amount_negative_tax_rate(calc):
    """Test calculate_tax_amount handles negative tax rates."""
    result = calc.calculate_tax_amount(100, -5)
    assert result == pytest.approx(-5.0)


def test_businesscalculator_calculate_net_present_value_basic(calc):
    """Test calculate_net_present_value returns correct NPV for typical case."""
    cash_flows = [100, 100, 100]
    discount_rate = 0.1
    expected = 100 / (1 + discount_rate) ** 0 + 100 / (1 + discount_rate) ** 1 + 100 / (1 + discount_rate) ** 2
    result = calc.calculate_net_present_value(cash_flows, discount_rate)
    assert result == pytest.approx(expected)


def test_businesscalculator_calculate_net_present_value_zero_discount(calc):
    """Test calculate_net_present_value with zero discount rate equals sum of cash flows."""
    cash_flows = [100, 200, 300]
    result = calc.calculate_net_present_value(cash_flows, 0.0)
    assert result == sum(cash_flows)


def test_businesscalculator_calculate_net_present_value_raises_with_discount_rate_minus_one(calc):
    """Test calculate_net_present_value raises ZeroDivisionError when discount_rate is -1."""
    cash_flows = [100, 200]
    with pytest.raises(ZeroDivisionError):
        calc.calculate_net_present_value(cash_flows, -1.0)


def test_businesscalculator_calculate_net_present_value_calls_math_pow(calc):
    """Test calculate_net_present_value calls math.pow for each period using correct arguments."""
    cash_flows = [50, 75, 100, 125]
    discount_rate = 0.05
    with patch("calculator.math.pow", wraps=math.pow) as mock_pow:
        result = calc.calculate_net_present_value(cash_flows, discount_rate)
        # Assert pow called once per cash flow
        assert mock_pow.call_count == len(cash_flows)
        # Verify first few calls include expected arguments
        expected_base = 1 + discount_rate
        # Extract the called args
        call_args_list = [call.args for call in mock_pow.call_args_list]
        assert call_args_list[0] == (expected_base, 0)
        assert call_args_list[1] == (expected_base, 1)
        assert call_args_list[2] == (expected_base, 2)
        # Sanity check on result against unmocked calculation
        expected = sum(cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows))
        assert result == pytest.approx(expected)


def test_businesscalculator_calculate_markup_percentage_basic(calc):
    """Test calculate_markup_percentage returns correct percentage for normal case."""
    result = calc.calculate_markup_percentage(80, 100)
    assert result == pytest.approx(25.0)


def test_businesscalculator_calculate_markup_percentage_cost_zero_returns_zero(calc):
    """Test calculate_markup_percentage returns 0 when cost is zero to avoid division by zero."""
    result = calc.calculate_markup_percentage(0, 100)
    assert result == 0


def test_businesscalculator_calculate_markup_percentage_negative(calc):
    """Test calculate_markup_percentage handles negative markup when selling price is below cost."""
    result = calc.calculate_markup_percentage(80, 60)
    assert result == pytest.approx(-25.0)