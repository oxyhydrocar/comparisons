import math
import pytest
from unittest.mock import patch

from calculator import BusinessCalculator


@pytest.fixture
def calculator_instance():
    """Create BusinessCalculator instance for testing"""
    return BusinessCalculator()


def test_business_calculator_initialization(calculator_instance):
    """Test that BusinessCalculator can be instantiated"""
    assert isinstance(calculator_instance, BusinessCalculator)


def test_business_calculator_calculate_profit_margin_basic(calculator_instance):
    """Test calculate_profit_margin with typical positive values"""
    result = calculator_instance.calculate_profit_margin(200, 50)
    expected = ((200 - 50) / 200) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_profit_margin_zero_revenue(calculator_instance):
    """Test calculate_profit_margin returns 0 when revenue is zero"""
    result = calculator_instance.calculate_profit_margin(0, 50)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_profit_margin_negative_margin(calculator_instance):
    """Test calculate_profit_margin with costs exceeding revenue (negative margin)"""
    result = calculator_instance.calculate_profit_margin(100, 150)
    expected = ((100 - 150) / 100) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_roi_basic(calculator_instance):
    """Test calculate_roi with typical gain and cost"""
    result = calculator_instance.calculate_roi(150, 100)
    expected = ((150 - 100) / 100) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_roi_zero_cost(calculator_instance):
    """Test calculate_roi returns 0 when cost is zero"""
    result = calculator_instance.calculate_roi(150, 0)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_roi_negative_roi(calculator_instance):
    """Test calculate_roi when gain is less than cost (negative ROI)"""
    result = calculator_instance.calculate_roi(80, 100)
    expected = ((80 - 100) / 100) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_compound_growth_rate_basic(calculator_instance):
    """Test calculate_compound_growth_rate with typical values"""
    result = calculator_instance.calculate_compound_growth_rate(100, 200, 2)
    expected = ((200 - 100) / 100) / 2 * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_compound_growth_rate_starting_non_positive(calculator_instance):
    """Test calculate_compound_growth_rate returns 0 when starting_value <= 0"""
    result = calculator_instance.calculate_compound_growth_rate(0, 200, 2)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_compound_growth_rate_periods_non_positive(calculator_instance):
    """Test calculate_compound_growth_rate returns 0 when periods <= 0"""
    result = calculator_instance.calculate_compound_growth_rate(100, 200, 0)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_compound_growth_rate_negative_growth(calculator_instance):
    """Test calculate_compound_growth_rate handles negative growth correctly"""
    result = calculator_instance.calculate_compound_growth_rate(100, 80, 4)
    expected = ((80 - 100) / 100) / 4 * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_break_even_point_basic(calculator_instance):
    """Test calculate_break_even_point computes expected break-even units"""
    result = calculator_instance.calculate_break_even_point(1000, 50, 30)
    expected = 1000 / (50 - 30)
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_break_even_point_no_contribution(calculator_instance):
    """Test calculate_break_even_point returns None when contribution margin <= 0"""
    result_equal = calculator_instance.calculate_break_even_point(1000, 30, 30)
    assert result_equal is None
    result_negative = calculator_instance.calculate_break_even_point(1000, 25, 30)
    assert result_negative is None


def test_business_calculator_calculate_discount_price_basic(calculator_instance):
    """Test calculate_discount_price applies percentage discount"""
    result = calculator_instance.calculate_discount_price(200, 25)
    expected = 200 - (200 * (25 / 100))
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_discount_price_negative_percentage(calculator_instance):
    """Test calculate_discount_price with negative discount percentage increases price"""
    result = calculator_instance.calculate_discount_price(200, -10)
    expected = 200 - (200 * (-10 / 100))
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_discount_price_over_100_percentage(calculator_instance):
    """Test calculate_discount_price with discount percentage over 100% leads to negative price"""
    result = calculator_instance.calculate_discount_price(200, 150)
    expected = 200 - (200 * (150 / 100))
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_tax_amount_basic(calculator_instance):
    """Test calculate_tax_amount computes tax from percentage rate"""
    result = calculator_instance.calculate_tax_amount(100, 7.5)
    expected = 100 * (7.5 / 100)
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_tax_amount_zero_rate(calculator_instance):
    """Test calculate_tax_amount returns 0 when tax rate is zero"""
    result = calculator_instance.calculate_tax_amount(100, 0)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_tax_amount_negative_rate(calculator_instance):
    """Test calculate_tax_amount supports negative tax rate resulting in negative tax amount"""
    result = calculator_instance.calculate_tax_amount(100, -5)
    expected = 100 * (-5 / 100)
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_basic(calculator_instance):
    """Test calculate_net_present_value with typical cash flows and rate"""
    cash_flows = [-100, 30, 40, 50]
    rate = 0.10
    result = calculator_instance.calculate_net_present_value(cash_flows, rate)
    expected = sum(cf / math.pow(1 + rate, t) for t, cf in enumerate(cash_flows))
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_zero_rate(calculator_instance):
    """Test calculate_net_present_value with zero discount rate equals sum of cash flows"""
    cash_flows = [-100, 30, 40, 50]
    rate = 0.0
    result = calculator_instance.calculate_net_present_value(cash_flows, rate)
    expected = sum(cash_flows)
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_net_present_value_calls_math_pow(calculator_instance):
    """Test calculate_net_present_value uses math.pow with expected arguments"""
    cash_flows = [10, 20, 30]
    rate = 0.05
    with patch('calculator.math.pow', wraps=math.pow) as mock_pow:
        result = calculator_instance.calculate_net_present_value(cash_flows, rate)
        expected = sum(cf / math.pow(1 + rate, t) for t, cf in enumerate(cash_flows))
        assert result == pytest.approx(expected)
        assert mock_pow.call_count == len(cash_flows)
        for t, call in enumerate(mock_pow.call_args_list):
            base_arg = call.args[0]
            exp_arg = call.args[1]
            assert base_arg == pytest.approx(1 + rate)
            assert exp_arg == t


def test_business_calculator_calculate_net_present_value_dependency_error_propagates(calculator_instance):
    """Test calculate_net_present_value propagates exceptions from math.pow"""
    cash_flows = [10, 20]
    rate = 0.1

    def boom(*args, **kwargs):
        raise RuntimeError("pow failure")

    with patch('calculator.math.pow', side_effect=boom):
        with pytest.raises(RuntimeError):
            calculator_instance.calculate_net_present_value(cash_flows, rate)


def test_business_calculator_calculate_markup_percentage_basic(calculator_instance):
    """Test calculate_markup_percentage with typical cost and selling price"""
    result = calculator_instance.calculate_markup_percentage(80, 100)
    expected = ((100 - 80) / 80) * 100
    assert result == pytest.approx(expected)


def test_business_calculator_calculate_markup_percentage_zero_cost(calculator_instance):
    """Test calculate_markup_percentage returns 0 when cost is zero"""
    result = calculator_instance.calculate_markup_percentage(0, 100)
    assert result == pytest.approx(0)


def test_business_calculator_calculate_markup_percentage_negative_markup(calculator_instance):
    """Test calculate_markup_percentage when selling price is below cost (negative markup)"""
    result = calculator_instance.calculate_markup_percentage(100, 90)
    expected = ((90 - 100) / 100) * 100
    assert result == pytest.approx(expected)