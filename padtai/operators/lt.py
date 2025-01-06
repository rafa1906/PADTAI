from . base import GroundedOperator


class LTOperator(GroundedOperator):
    """
    A class used to represent the less-than operator.

    The less-than operator compares two numbers i,j and stores the result as lt(i, j).

    Methods:
        operator(): Returns the string "lt" representing the less-than operator.
        arity(): Returns the arity of the less-than operator (2).
        ground(int_list): Grounds the less-than operator on sorted list of integers/floats.
        query(int_pair): Defines Janus query for the less-than operator on arbitrary pair 
                         of integers/floats.
    """

    def operator(self):
        """
        Returns the string "lt" representing the less-than operator.

        Returns:
            str: The string "lt".
        """

        return "lt"


    def arity(self):
        """
        Returns the arity of the less-than operator (2).

        Returns:
            int: The arity of the less-than operator (2).
        """

        return 2


    def ground(self, int_list):
        """
        Generates pair relations for the less-than operator.

        Iterates over int_list with indices i,j s.t. i + 1 <= j. 
        This is equivalent to int_list[i] < int_list[j] because the list is sorted.

        Parameters:
            int_list (list of int and float): A sorted list of integers/floats.

        Returns:
            list of str: A list of pair relations in the format "lt({i},{j}).".
        """

        facts = []
        for i in range(len(int_list)):
            for j in range (i + 1, len(int_list)):
                facts += ["lt({},{}).".format(int_list[i], int_list[j])]

        return facts
    
    
    def query(self, int_pair):
        """
        Asserts the less-than relation for an integer pair i,j s.t. i < j.

        If the condition i < j is not met, returns empty query.

        Parameters:
            int_pair (tuple of (int or float, int or float)): A pair of integers/floats.

        Returns:
            tuple: A tuple containing a string and a dictionary:
                - str: A Janus query.
                - dict: A dictionary containing input bindings.
                If the condition i < j is not met, returns empty query and dictionary.
        """

        if int_pair[0] < int_pair[1]:
            return "assert(lt(Vi,Vj))", { "Vi": int_pair[0], "Vj": int_pair[1] }
        else:
            return "", {}
