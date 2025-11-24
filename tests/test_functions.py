"""Tests for user-defined functions."""

import pytest

from notebook.document import Document, FormulaBlock


def test_simple_function_definition() -> None:
    """Function definitions should be parsed and stored correctly."""

    func_block = FormulaBlock("f(x) = x**2 + 2*x + 1")
    func_block.evaluate()

    assert func_block.is_function_def is True
    assert func_block.function_name == "f"
    assert func_block.function_params == ["x"]
    assert func_block.evaluation_status == "ok"
    assert "Function f(x) defined" in func_block.result


def test_multi_parameter_function() -> None:
    """Functions with multiple parameters should work correctly."""

    func_block = FormulaBlock("area(b, h) = b * h / 2")
    func_block.evaluate()

    assert func_block.is_function_def is True
    assert func_block.function_name == "area"
    assert func_block.function_params == ["b", "h"]
    assert func_block.evaluation_status == "ok"


def test_function_call_single_param() -> None:
    """Calling a user-defined function should evaluate correctly."""

    f_def = FormulaBlock("f(x) = x**2")
    f_call = FormulaBlock("result = f(5)")

    doc = Document([f_def, f_call])
    doc.evaluate()

    assert f_call.numeric_value == pytest.approx(25.0)
    assert f_call.result == "25.00"


def test_function_call_multiple_params() -> None:
    """Functions with multiple parameters should evaluate correctly."""

    area_def = FormulaBlock("area(b, h) = b * h / 2")
    area_call = FormulaBlock("A = area(10, 5)")

    doc = Document([area_def, area_call])
    doc.evaluate()

    assert area_call.numeric_value == pytest.approx(25.0)
    assert area_call.result == "25.00"


def test_function_composition() -> None:
    """Functions can reference other functions."""

    f_def = FormulaBlock("f(x) = x**2")
    g_def = FormulaBlock("g(x) = f(x) + 10")
    g_call = FormulaBlock("result = g(3)")

    doc = Document([f_def, g_def, g_call])
    doc.evaluate()

    assert g_call.numeric_value == pytest.approx(19.0)  # 3**2 + 10 = 19


def test_function_with_variables() -> None:
    """Functions can use previously defined variables."""

    var_block = FormulaBlock("c = 5")
    func_def = FormulaBlock("h(x) = x + c")
    func_call = FormulaBlock("result = h(10)")

    doc = Document([var_block, func_def, func_call])
    doc.evaluate()

    assert func_call.numeric_value == pytest.approx(15.0)


def test_function_in_expression() -> None:
    """Functions can be used in complex expressions."""

    func_def = FormulaBlock("square(x) = x**2")
    expr = FormulaBlock("result = 2 * square(3) + 5")

    doc = Document([func_def, expr])
    doc.evaluate()

    assert expr.numeric_value == pytest.approx(23.0)  # 2 * 9 + 5 = 23


def test_function_not_defined_error() -> None:
    """Calling an undefined function should produce an error."""

    call = FormulaBlock("result = undefined_func(5)")
    call.evaluate()

    assert call.evaluation_status == "error"
    assert call.numeric_value is None


def test_function_latex_rendering() -> None:
    """Function definitions should render properly in LaTeX."""

    func_block = FormulaBlock("f(x) = x**2 + 1")
    func_block.evaluate()

    assert func_block.latex is not None
    assert "f(x)" in func_block.latex
    assert "x^{2}" in func_block.latex or "x ^ { 2 }" in func_block.latex


def test_function_with_built_in_math() -> None:
    """Functions can use built-in math functions."""

    func_def = FormulaBlock("hypotenuse(a, b) = sqrt(a**2 + b**2)")
    func_call = FormulaBlock("c = hypotenuse(3, 4)")

    doc = Document([func_def, func_call])
    doc.evaluate()

    assert func_call.numeric_value == pytest.approx(5.0)


def test_multiple_functions() -> None:
    """Multiple functions can coexist in the same document."""

    f1 = FormulaBlock("double(x) = 2 * x")
    f2 = FormulaBlock("triple(x) = 3 * x")
    call1 = FormulaBlock("a = double(5)")
    call2 = FormulaBlock("b = triple(5)")

    doc = Document([f1, f2, call1, call2])
    context = doc.evaluate()

    assert call1.numeric_value == pytest.approx(10.0)
    assert call2.numeric_value == pytest.approx(15.0)
    assert len(context.functions) == 2
