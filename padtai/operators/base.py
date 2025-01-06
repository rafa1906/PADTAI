from typing import Union, Tuple, List


class GroundedOperator:
    """
    The base class for operators to be grounded.

    Methods:
        operator(): Returns the name of the operator.
        arity(): Returns the arity of the operator.
        ground(int_list): Grounds the operator on sorted list of integers/floats.
        query(int_pair): Defines Janus query on arbitrary pair of integers/floats.
    """

    def operator(self) -> str:
        """
        Allows the developer to define name of the operator.

        Returns:
            str: The name of the operator.
        """

        pass


    def arity(self) -> int:
        """
        Allows the developer to define arity of operator.

        Returns:
            int: The arity of the operator.
        """

        pass


    def ground(self, int_list: List[Union[int, float]]) -> List[str]:
        """
        Allows the developer to define grounding operation.

        Parameters:
            int_list (list of int and float): A sorted list of integers/floats.

        Returns:
            list of str: A list of pair relations.
        """

        pass


    def query(self, int_pair: Tuple[Union[int, float], Union[int, float]]) -> Tuple[str, dict]:
        """
        Allows the developer to define Janus query on arbitrary pair of integers/floats.

        Parameters:
            int_pair (tuple of (int or float, int or float)): A pair of integers/floats.
        
        Returns:
            tuple: A tuple containing a string and a dictionary:
                - str: A Janus query.
                - dict: A dictionary containing input bindings.
        """

        pass
