from datetime import datetime
from datetime import timedelta
from ..helpers.utils import generate_interval_string
from enum import Enum


class WhereOperatorEnum(Enum):
    LT = 'lt'
    LTE = 'lte'
    GT = 'gt'
    GTE = 'gte'
    EQ = 'eq'
    NE = 'ne'
    RE = 're'
    NRE = 'nre'
    ADD = 'add'
    SUB = 'sub'
    MULT = 'mult'
    DIV = 'div'
    MOD = 'mod'


EVALUATED_OPERATORS = {
    WhereOperatorEnum.LT: '<',
    WhereOperatorEnum.LTE: '<=',
    WhereOperatorEnum.GT: '>',
    WhereOperatorEnum.GTE: '>=',
    WhereOperatorEnum.EQ: '=',
    WhereOperatorEnum.NE: '!=',
    WhereOperatorEnum.RE: '=~',
    WhereOperatorEnum.NRE: '!~',
    WhereOperatorEnum.ADD: '+',
    WhereOperatorEnum.SUB: '-',
    WhereOperatorEnum.MULT: '*',
    WhereOperatorEnum.DIV: '/',
    WhereOperatorEnum.MOD: '%',
}

INVERTED_OPERATORS = {
    WhereOperatorEnum.LT: WhereOperatorEnum.GTE,
    WhereOperatorEnum.LTE: WhereOperatorEnum.GT,
    WhereOperatorEnum.GT: WhereOperatorEnum.LTE,
    WhereOperatorEnum.GTE: WhereOperatorEnum.LT,
    WhereOperatorEnum.EQ: WhereOperatorEnum.NE,
    WhereOperatorEnum.NE: WhereOperatorEnum.EQ,
    WhereOperatorEnum.RE: WhereOperatorEnum.NRE,
    WhereOperatorEnum.NRE: WhereOperatorEnum.RE,
    WhereOperatorEnum.ADD: WhereOperatorEnum.SUB,
    WhereOperatorEnum.SUB: WhereOperatorEnum.ADD,
    WhereOperatorEnum.MULT: WhereOperatorEnum.DIV,
    WhereOperatorEnum.DIV: WhereOperatorEnum.MULT,
    WhereOperatorEnum.MOD: WhereOperatorEnum.MOD,
}


class Field:

    def __init__(self, field_name):
        self.field_name = field_name

    def __lt__(self, value):
        return Criteria(self, value, WhereOperatorEnum.LT)

    def __le__(self, value):
        return Criteria(self, value, WhereOperatorEnum.LTE)

    def __eq__(self, value):
        return Criteria(self, value, WhereOperatorEnum.EQ)

    def __ne__(self, value):
        return Criteria(self, value, WhereOperatorEnum.NE)

    def __ge__(self, value):
        return Criteria(self, value, WhereOperatorEnum.GTE)

    def __gt__(self, value):
        return Criteria(self, value, WhereOperatorEnum.GT)

    def __add__(self, other):
        return MathCriteria(self, other, WhereOperatorEnum.ADD)

    def __sub__(self, other):
        return MathCriteria(self, other, WhereOperatorEnum.SUB)

    def __mul__(self, other):
        return MathCriteria(self, other, WhereOperatorEnum.MULT)

    def __div__(self, other):
        return MathCriteria(self, other, WhereOperatorEnum.DIV)

    def __mod__(self, other):
        return MathCriteria(self, other, WhereOperatorEnum.MOD)

    def regex(self, value):
        return Criteria(self, f"\\{value}\\", WhereOperatorEnum.RE)

    def __contains__(self, items):
        return DisjunctionCriteria(*[Criteria(self, item, WhereOperatorEnum.EQ) for item in list(items)])

    def __str__(self):
        return self.field_name


class MathCriteria:
    def __init__(self, left_operand, right_operand, operator):
        self.left_operand = left_operand
        self.right_operand = right_operand
        self.operator = operator

    def __lt__(self, value):
        return Criteria(self, value, WhereOperatorEnum.LT)

    def __le__(self, value):
        return Criteria(self, value, WhereOperatorEnum.LTE)

    def __eq__(self, value):
        return Criteria(self, value, WhereOperatorEnum.EQ)

    def __ne__(self, value):
        return Criteria(self, value, WhereOperatorEnum.NE)

    def __ge__(self, value):
        return Criteria(self, value, WhereOperatorEnum.GTE)

    def __gt__(self, value):
        return Criteria(self, value, WhereOperatorEnum.GT)

    def evaluate(self):
        if hasattr(self.left_operand, 'evaluate'):
            left_operand = self.left_operand.evaluate()
        else:
            left_operand = '"{}"'.format(self.left_operand)
        operator = EVALUATED_OPERATORS[self.operator]
        right_operand = self.right_operand
        if isinstance(right_operand, Field):
            right_operand = '"{}"'.format(self.right_operand)
        return '{} {} {}'.format(left_operand, operator, right_operand)


class Criteria:
    def __init__(self, left_operand, right_operand, operator):
        self.left_operand = left_operand
        self.right_operand = right_operand
        self.operator = operator

    def __invert__(self):
        inverted_operator = INVERTED_OPERATORS[self.operator]
        return Criteria(
            self.left_operand,
            self.right_operand,
            inverted_operator,
        )

    def __or__(self, criteria):
        return DisjunctionCriteria(self, criteria)

    def evaluate(self):
        if hasattr(self.left_operand, 'evaluate'):
            left_operand = self.left_operand.evaluate()
        else:
            left_operand = '"{}"'.format(self.left_operand)
        operator = EVALUATED_OPERATORS[self.operator]
        right_operand = self.right_operand
        if isinstance(right_operand, datetime):
            right_operand = right_operand.strftime('%Y-%m-%dT%H:%M:%SZ')
        if isinstance(right_operand, str):
            right_operand = '\'{}\''.format(self.right_operand)
        elif isinstance(right_operand, timedelta):
            right_operand = generate_interval_string(right_operand)
        else:
            if hasattr(right_operand, 'evaluate'):
                right_operand = right_operand.evaluate()
        return '{} {} {}'.format(left_operand, operator, right_operand)

    def __str__(self):
        return 'CRITERIA: {} {} {}'.format(
            self.left_operand,
            EVALUATED_OPERATORS[self.operator],
            self.right_operand,
        )


class DisjunctionCriteria:
    def __init__(self, left_criteria, right_criteria):
        self.left_criteria = left_criteria
        self.right_criteria = right_criteria

    def __or__(self, criteria):
        return DisjunctionCriteria(self, criteria)

    def __and__(self, criteria):
        return InjunctionCriteria(self, criteria)

    def evaluate(self):
        left_criteria = '({}'.format(self.left_criteria.evaluate())
        right_criteria = '{})'.format(self.right_criteria.evaluate())
        return ' OR '.join([left_criteria, right_criteria])


class InjunctionCriteria:
    def __init__(self, left_criteria, right_criteria):
        self.left_criteria = left_criteria
        self.right_criteria = right_criteria

    def __or__(self, criteria):
        return DisjunctionCriteria(self, criteria)

    def __and__(self, criteria):
        return InjunctionCriteria(self, criteria)

    def evaluate(self):
        left_criteria = '({}'.format(self.left_criteria.evaluate())
        right_criteria = '{})'.format(self.right_criteria.evaluate())
        return ' AND '.join([left_criteria, right_criteria])
