# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# %% [python]
# Active Python code block  # noqa: E305,E501
import math
import os

def test_function(x):
    """Test function with docstring."""
    return x * 2

result = test_function(5)
print(f"Result: {result}")
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# -
# %% [python]
# Another Python block with potential linting issues  # noqa: E305,E501
def badfunction(list):  # Using "list" as parameter name (should trigger pylint)
    return list

# Line with long comment that might exceed character limits for linting purposes and should be caught by pylint tools
x=1+2+3+4+5  # No spaces around operators
# -
# -
# -
