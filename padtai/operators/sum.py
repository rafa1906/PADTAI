from . base import GroundedOperator


class SumOperator(GroundedOperator):
    """
    A class used to represent the sum operator.

    The sum operator adds two numbers i,j and stores the result as sum(i, j, i + j).

    Methods:
        operator(): Returns the string "sum" representing the sum operator.
        arity(): Returns the arity of the sum operator (3).
        ground(int_list): Grounds the sum operator on sorted list of integers/floats.
        query(int_pair): Defines Janus query for the sum operator on arbitrary pair 
                         of integers/floats.
    """

    def operator(self):
        """
        Returns the string "sum" representing the sum operator.

        Returns:
            str: The string "sum".
        """

        return "sum"


    def arity(self):
        """
        Returns the arity of the sum operator (3).

        Returns:
            int: The arity of the sum operator (3).
        """

        return 3

    def ground(self, int_list):
        """
        Generates pair relations for the less-than operator.

        Iterates over int_list with indices i,j s.t. i <= j.
        This is exhaustive because sum is commutative, i.e.,
        int_list[i] + int_list[j] = int_list[j] + int_list[i].

        Parameters:
            int_list (list of int and float): A sorted list of integers/floats.

        Returns:
            list of str: A list of pair relations in the format "sum({i},{j},{i+j}).".
        """

        facts = []
        for i in range(len(int_list)):
            for j in range (i, len(int_list)):
                facts += ["sum({},{},{}).".format(int_list[i], int_list[j], \
                                                  int_list[i] + int_list[j])]
                
        return facts
    
    def query(self, int_pair):
        """
        Asserts the sum relation for an integer pair i,j s.t. k = i + j.

        Parameters:
            int_pair (tuple of (int or float, int or float)): A pair of integers/floats.

        Returns:
            tuple: A tuple containing a string and a dictionary:
                - str: A Janus query.
                - dict: A dictionary containing input bindings.
        """

        return "assert(sum(Vi,Vj,Vk))", { "Vi": int_pair[0], "Vj": int_pair[1], \
                                          "Vk": int_pair[0] + int_pair[1] }