topics = {'assert':
    """The "assert" statement
**********************

Assert statements are a convenient way to insert debugging assertions
into a program:

   assert_stmt ::= "assert" expression ["," expression]

The simple form, "assert expression", is equivalent to

   if __debug__:
       if not expression: raise AssertionError

The extended form, "assert expression1, expression2", is equivalent to

   if __debug__:
       if not expression1: raise AssertionError(expression2)

These equivalences assume that "__debug__" and "AssertionError" refer
to the built-in variables with those names.  In the current
implementation, the built-in variable "__debug__" is "True" under
normal circumstances, "False" when optimization is requested (command
line option -O).  The current code generator emits no code for an
assert statement when optimization is requested at compile time.  Note
that it is unnecessary to include the source code for the expression
that failed in the error message; it will be displayed as part of the
stack trace.

Assignments to "__debug__" are illegal.  The value for the built-in
variable is determined when the interpreter starts.
"""
    , 'assignment':
    """Assignment statements
*********************

Assignment statements are used to (re)bind names to values and to
modify attributes or items of mutable objects:

   assignment_stmt ::= (target_list "=")+ (starred_expression | yield_expression)
   target_list     ::= target ("," target)* [","]
   target          ::= identifier
              | "(" [target_list] ")"
              | "[" [target_list] "]"
              | attributeref
              | subscription
              | slicing
              | "*" target

(See section Primaries for the syntax definitions for *attributeref*,
*subscription*, and *slicing*.)

An assignment statement evaluates the expression list (remember that
this can be a single expression or a comma-separated list, the latter
yielding a tuple) and assigns the single resulting object to each of
the target lists, from left to right.

Assignment is defined recursively depending on the form of the target
(list). When a target is part of a mutable object (an attribute
reference, subscription or slicing), the mutable object must
ultimately perform the assignment and decide about its validity, and
may raise an exception if the assignment is unacceptable.  The rules
observed by various types and the exceptions raised are given with the
definition of the object types (see section The standard type
hierarchy).

Assignment of an object to a target list, optionally enclosed in
parentheses or square brackets, is recursively defined as follows.

* If the target list is empty: The object must also be an empty
  iterable.

* If the target list is a single target in parentheses: The object
  is assigned to that target.

* If the target list is a comma-separated list of targets, or a
  single target in square brackets: The object must be an iterable
  with the same number of items as there are targets in the target
  list, and the items are assigned, from left to right, to the
  corresponding targets.

  * If the target list contains one target prefixed with an
    asterisk, called a "starred" target: The object must be an
    iterable with at least as many items as there are targets in the
    target list, minus one.  The first items of the iterable are
    assigned, from left to right, to the targets before the starred
    target.  The final items of the iterable are assigned to the
    targets after the starred target.  A list of the remaining items
    in the iterable is then assigned to the starred target (the list
    can be empty).

  * Else: The object must be an iterable with the same number of
    items as there are targets in the target list, and the items are
    assigned, from left to right, to the corresponding targets.

Assignment of an object to a single target is recursively defined as
follows.

* If the target is an identifier (name):

  * If the name does not occur in a "global" or "nonlocal" statement
    in the current code block: the name is bound to the object in the
    current local namespace.

  * Otherwise: the name is bound to the object in the global
    namespace or the outer namespace determined by "nonlocal",
    respectively.

  The name is rebound if it was already bound.  This may cause the
  reference count for the object previously bound to the name to reach
  zero, causing the object to be deallocated and its destructor (if it
  has one) to be called.

* If the target is an attribute reference: The primary expression in
  the reference is evaluated.  It should yield an object with
  assignable attributes; if this is not the case, "TypeError" is
  raised.  That object is then asked to assign the assigned object to
  the given attribute; if it cannot perform the assignment, it raises
  an exception (usually but not necessarily "AttributeError").

  Note: If the object is a class instance and the attribute reference
  occurs on both sides of the assignment operator, the RHS expression,
  "a.x" can access either an instance attribute or (if no instance
  attribute exists) a class attribute.  The LHS target "a.x" is always
  set as an instance attribute, creating it if necessary.  Thus, the
  two occurrences of "a.x" do not necessarily refer to the same
  attribute: if the RHS expression refers to a class attribute, the
  LHS creates a new instance attribute as the target of the
  assignment:

     class Cls:
         x = 3             # class variable
     inst = Cls()
     inst.x = inst.x + 1   # writes inst.x as 4 leaving Cls.x as 3

  This description does not necessarily apply to descriptor
  attributes, such as properties created with "property()".

* If the target is a subscription: The primary expression in the
  reference is evaluated.  It should yield either a mutable sequence
  object (such as a list) or a mapping object (such as a dictionary).
  Next, the subscript expression is evaluated.

  If the primary is a mutable sequence object (such as a list), the
  subscript must yield an integer.  If it is negative, the sequence's
  length is added to it.  The resulting value must be a nonnegative
  integer less than the sequence's length, and the sequence is asked
  to assign the assigned object to its item with that index.  If the
  index is out of range, "IndexError" is raised (assignment to a
  subscripted sequence cannot add new items to a list).

  If the primary is a mapping object (such as a dictionary), the
  subscript must have a type compatible with the mapping's key type,
  and the mapping is then asked to create a key/datum pair which maps
  the subscript to the assigned object.  This can either replace an
  existing key/value pair with the same key value, or insert a new
  key/value pair (if no key with the same value existed).

  For user-defined objects, the "__setitem__()" method is called with
  appropriate arguments.

* If the target is a slicing: The primary expression in the
  reference is evaluated.  It should yield a mutable sequence object
  (such as a list).  The assigned object should be a sequence object
  of the same type.  Next, the lower and upper bound expressions are
  evaluated, insofar they are present; defaults are zero and the
  sequence's length.  The bounds should evaluate to integers. If
  either bound is negative, the sequence's length is added to it.  The
  resulting bounds are clipped to lie between zero and the sequence's
  length, inclusive.  Finally, the sequence object is asked to replace
  the slice with the items of the assigned sequence.  The length of
  the slice may be different from the length of the assigned sequence,
  thus changing the length of the target sequence, if the target
  sequence allows it.

**CPython implementation detail:** In the current implementation, the
syntax for targets is taken to be the same as for expressions, and
invalid syntax is rejected during the code generation phase, causing
less detailed error messages.

Although the definition of assignment implies that overlaps between
the left-hand side and the right-hand side are 'simultaneous' (for
example "a, b = b, a" swaps two variables), overlaps *within* the
collection of assigned-to variables occur left-to-right, sometimes
resulting in confusion.  For instance, the following program prints
"[0, 2]":

   x = [0, 1]
   i = 0
   i, x[i] = 1, 2         # i is updated, then x[i] is updated
   print(x)

See also:

  **PEP 3132** - Extended Iterable Unpacking
     The specification for the "*target" feature.


Augmented assignment statements
===============================

Augmented assignment is the combination, in a single statement, of a
binary operation and an assignment statement:

   augmented_assignment_stmt ::= augtarget augop (expression_list | yield_expression)
   augtarget                 ::= identifier | attributeref | subscription | slicing
   augop                     ::= "+=" | "-=" | "*=" | "@=" | "/=" | "//=" | "%=" | "**="
             | ">>=" | "<<=" | "&=" | "^=" | "|="

(See section Primaries for the syntax definitions of the last three
symbols.)

An augmented assignment evaluates the target (which, unlike normal
assignment statements, cannot be an unpacking) and the expression
list, performs the binary operation specific to the type of assignment
on the two operands, and assigns the result to the original target.
The target is only evaluated once.

An augmented assignment expression like "x += 1" can be rewritten as
"x = x + 1" to achieve a similar, but not exactly equal effect. In the
augmented version, "x" is only evaluated once. Also, when possible,
the actual operation is performed *in-place*, meaning that rather than
creating a new object and assigning that to the target, the old object
is modified instead.

Unlike normal assignments, augmented assignments evaluate the left-
hand side *before* evaluating the right-hand side.  For example, "a[i]
+= f(x)" first looks-up "a[i]", then it evaluates "f(x)" and performs
the addition, and lastly, it writes the result back to "a[i]".

With the exception of assigning to tuples and multiple targets in a
single statement, the assignment done by augmented assignment
statements is handled the same way as normal assignments. Similarly,
with the exception of the possible *in-place* behavior, the binary
operation performed by augmented assignment is the same as the normal
binary operations.

For targets which are attribute references, the same caveat about
class and instance attributes applies as for regular assignments.


Annotated assignment statements
===============================

Annotation assignment is the combination, in a single statement, of a
variable or attribute annotation and an optional assignment statement:

   annotated_assignment_stmt ::= augtarget ":" expression ["=" expression]

The difference from normal Assignment statements is that only single
target and only single right hand side value is allowed.

For simple names as assignment targets, if in class or module scope,
the annotations are evaluated and stored in a special class or module
attribute "__annotations__" that is a dictionary mapping from variable
names (mangled if private) to evaluated annotations. This attribute is
writable and is automatically created at the start of class or module
body execution, if annotations are found statically.

For expressions as assignment targets, the annotations are evaluated
if in class or module scope, but not stored.

If a name is annotated in a function scope, then this name is local
for that scope. Annotations are never evaluated and stored in function
scopes.

If the right hand side is present, an annotated assignment performs
the actual assignment before evaluating annotations (where
applicable). If the right hand side is not present for an expression
target, then the interpreter evaluates the target except for the last
"__setitem__()" or "__setattr__()" call.

See also: **PEP 526** - Variable and attribute annotation syntax
  **PEP 484** - Type hints
"""
    , 'atom-identifiers':
    """Identifiers (Names)
*******************

An identifier occurring as an atom is a name.  See section Identifiers
and keywords for lexical definition and section Naming and binding for
documentation of naming and binding.

When the name is bound to an object, evaluation of the atom yields
that object. When a name is not bound, an attempt to evaluate it
raises a "NameError" exception.

**Private name mangling:** When an identifier that textually occurs in
a class definition begins with two or more underscore characters and
does not end in two or more underscores, it is considered a *private
name* of that class. Private names are transformed to a longer form
before code is generated for them.  The transformation inserts the
class name, with leading underscores removed and a single underscore
inserted, in front of the name.  For example, the identifier "__spam"
occurring in a class named "Ham" will be transformed to "_Ham__spam".
This transformation is independent of the syntactical context in which
the identifier is used.  If the transformed name is extremely long
(longer than 255 characters), implementation defined truncation may
happen. If the class name consists only of underscores, no
transformation is done.
"""
    , 'atom-literals':
    """Literals
********

Python supports string and bytes literals and various numeric
literals:

   literal ::= stringliteral | bytesliteral
               | integer | floatnumber | imagnumber

Evaluation of a literal yields an object of the given type (string,
bytes, integer, floating point number, complex number) with the given
value.  The value may be approximated in the case of floating point
and imaginary (complex) literals.  See section Literals for details.

All literals correspond to immutable data types, and hence the
object's identity is less important than its value.  Multiple
evaluations of literals with the same value (either the same
occurrence in the program text or a different occurrence) may obtain
the same object or a different object with the same value.
"""
    , 'attribute-access':
    """Customizing attribute access
****************************

The following methods can be defined to customize the meaning of
attribute access (use of, assignment to, or deletion of "x.name") for
class instances.

object.__getattr__(self, name)

   Called when an attribute lookup has not found the attribute in the
   usual places (i.e. it is not an instance attribute nor is it found
   in the class tree for "self").  "name" is the attribute name. This
   method should return the (computed) attribute value or raise an
   "AttributeError" exception.

   Note that if the attribute is found through the normal mechanism,
   "__getattr__()" is not called.  (This is an intentional asymmetry
   between "__getattr__()" and "__setattr__()".) This is done both for
   efficiency reasons and because otherwise "__getattr__()" would have
   no way to access other attributes of the instance.  Note that at
   least for instance variables, you can fake total control by not
   inserting any values in the instance attribute dictionary (but
   instead inserting them in another object).  See the
   "__getattribute__()" method below for a way to actually get total
   control over attribute access.

object.__getattribute__(self, name)

   Called unconditionally to implement attribute accesses for
   instances of the class. If the class also defines "__getattr__()",
   the latter will not be called unless "__getattribute__()" either
   calls it explicitly or raises an "AttributeError". This method
   should return the (computed) attribute value or raise an
   "AttributeError" exception. In order to avoid infinite recursion in
   this method, its implementation should always call the base class
   method with the same name to access any attributes it needs, for
   example, "object.__getattribute__(self, name)".

   Note: This method may still be bypassed when looking up special
     methods as the result of implicit invocation via language syntax
     or built-in functions. See Special method lookup.

object.__setattr__(self, name, value)

   Called when an attribute assignment is attempted.  This is called
   instead of the normal mechanism (i.e. store the value in the
   instance dictionary). *name* is the attribute name, *value* is the
   value to be assigned to it.

   If "__setattr__()" wants to assign to an instance attribute, it
   should call the base class method with the same name, for example,
   "object.__setattr__(self, name, value)".

object.__delattr__(self, name)

   Like "__setattr__()" but for attribute deletion instead of
   assignment.  This should only be implemented if "del obj.name" is
   meaningful for the object.

object.__dir__(self)

   Called when "dir()" is called on the object. A sequence must be
   returned. "dir()" converts the returned sequence to a list and
   sorts it.


Implementing Descriptors
========================

The following methods only apply when an instance of the class
containing the method (a so-called *descriptor* class) appears in an
*owner* class (the descriptor must be in either the owner's class
dictionary or in the class dictionary for one of its parents).  In the
examples below, "the attribute" refers to the attribute whose name is
the key of the property in the owner class' "__dict__".

object.__get__(self, instance, owner)

   Called to get the attribute of the owner class (class attribute
   access) or of an instance of that class (instance attribute
   access). *owner* is always the owner class, while *instance* is the
   instance that the attribute was accessed through, or "None" when
   the attribute is accessed through the *owner*.  This method should
   return the (computed) attribute value or raise an "AttributeError"
   exception.

object.__set__(self, instance, value)

   Called to set the attribute on an instance *instance* of the owner
   class to a new value, *value*.

object.__delete__(self, instance)

   Called to delete the attribute on an instance *instance* of the
   owner class.

object.__set_name__(self, owner, name)

   Called at the time the owning class *owner* is created. The
   descriptor has been assigned to *name*.

   New in version 3.6.

The attribute "__objclass__" is interpreted by the "inspect" module as
specifying the class where this object was defined (setting this
appropriately can assist in runtime introspection of dynamic class
attributes). For callables, it may indicate that an instance of the
given type (or a subclass) is expected or required as the first
positional argument (for example, CPython sets this attribute for
unbound methods that are implemented in C).


Invoking Descriptors
====================

In general, a descriptor is an object attribute with "binding
behavior", one whose attribute access has been overridden by methods
in the descriptor protocol:  "__get__()", "__set__()", and
"__delete__()". If any of those methods are defined for an object, it
is said to be a descriptor.

The default behavior for attribute access is to get, set, or delete
the attribute from an object's dictionary. For instance, "a.x" has a
lookup chain starting with "a.__dict__['x']", then
"type(a).__dict__['x']", and continuing through the base classes of
"type(a)" excluding metaclasses.

However, if the looked-up value is an object defining one of the
descriptor methods, then Python may override the default behavior and
invoke the descriptor method instead.  Where this occurs in the
precedence chain depends on which descriptor methods were defined and
how they were called.

The starting point for descriptor invocation is a binding, "a.x". How
the arguments are assembled depends on "a":

Direct Call
   The simplest and least common call is when user code directly
   invokes a descriptor method:    "x.__get__(a)".

Instance Binding
   If binding to an object instance, "a.x" is transformed into the
   call: "type(a).__dict__['x'].__get__(a, type(a))".

Class Binding
   If binding to a class, "A.x" is transformed into the call:
   "A.__dict__['x'].__get__(None, A)".

Super Binding
   If "a" is an instance of "super", then the binding "super(B,
   obj).m()" searches "obj.__class__.__mro__" for the base class "A"
   immediately preceding "B" and then invokes the descriptor with the
   call: "A.__dict__['m'].__get__(obj, obj.__class__)".

For instance bindings, the precedence of descriptor invocation depends
on the which descriptor methods are defined.  A descriptor can define
any combination of "__get__()", "__set__()" and "__delete__()".  If it
does not define "__get__()", then accessing the attribute will return
the descriptor object itself unless there is a value in the object's
instance dictionary.  If the descriptor defines "__set__()" and/or
"__delete__()", it is a data descriptor; if it defines neither, it is
a non-data descriptor.  Normally, data descriptors define both
"__get__()" and "__set__()", while non-data descriptors have just the
"__get__()" method.  Data descriptors with "__set__()" and "__get__()"
defined always override a redefinition in an instance dictionary.  In
contrast, non-data descriptors can be overridden by instances.

Python methods (including "staticmethod()" and "classmethod()") are
implemented as non-data descriptors.  Accordingly, instances can
redefine and override methods.  This allows individual instances to
acquire behaviors that differ from other instances of the same class.

The "property()" function is implemented as a data descriptor.
Accordingly, instances cannot override the behavior of a property.


__slots__
=========

By default, instances of classes have a dictionary for attribute
storage.  This wastes space for objects having very few instance
variables.  The space consumption can become acute when creating large
numbers of instances.

The default can be overridden by defining *__slots__* in a class
definition. The *__slots__* declaration takes a sequence of instance
variables and reserves just enough space in each instance to hold a
value for each variable.  Space is saved because *__dict__* is not
created for each instance.

object.__slots__

   This class variable can be assigned a string, iterable, or sequence
   of strings with variable names used by instances.  *__slots__*
   reserves space for the declared variables and prevents the
   automatic creation of *__dict__* and *__weakref__* for each
   instance.


Notes on using *__slots__*
--------------------------

* When inheriting from a class without *__slots__*, the *__dict__*
  attribute of that class will always be accessible, so a *__slots__*
  definition in the subclass is meaningless.

* Without a *__dict__* variable, instances cannot be assigned new
  variables not listed in the *__slots__* definition.  Attempts to
  assign to an unlisted variable name raises "AttributeError". If
  dynamic assignment of new variables is desired, then add
  "'__dict__'" to the sequence of strings in the *__slots__*
  declaration.

* Without a *__weakref__* variable for each instance, classes
  defining *__slots__* do not support weak references to its
  instances. If weak reference support is needed, then add
  "'__weakref__'" to the sequence of strings in the *__slots__*
  declaration.

* *__slots__* are implemented at the class level by creating
  descriptors (Implementing Descriptors) for each variable name.  As a
  result, class attributes cannot be used to set default values for
  instance variables defined by *__slots__*; otherwise, the class
  attribute would overwrite the descriptor assignment.

* The action of a *__slots__* declaration is limited to the class
  where it is defined.  As a result, subclasses will have a *__dict__*
  unless they also define *__slots__* (which must only contain names
  of any *additional* slots).

* If a class defines a slot also defined in a base class, the
  instance variable defined by the base class slot is inaccessible
  (except by retrieving its descriptor directly from the base class).
  This renders the meaning of the program undefined.  In the future, a
  check may be added to prevent this.

* Nonempty *__slots__* does not work for classes derived from
  "variable-length" built-in types such as "int", "bytes" and "tuple".

* Any non-string iterable may be assigned to *__slots__*. Mappings
  may also be used; however, in the future, special meaning may be
  assigned to the values corresponding to each key.

* *__class__* assignment works only if both classes have the same
  *__slots__*.
"""
    , 'attribute-references':
    """Attribute references
********************

An attribute reference is a primary followed by a period and a name:

   attributeref ::= primary "." identifier

The primary must evaluate to an object of a type that supports
attribute references, which most objects do.  This object is then
asked to produce the attribute whose name is the identifier.  This
production can be customized by overriding the "__getattr__()" method.
If this attribute is not available, the exception "AttributeError" is
raised.  Otherwise, the type and value of the object produced is
determined by the object.  Multiple evaluations of the same attribute
reference may yield different objects.
"""
    , 'augassign':
    """Augmented assignment statements
*******************************

Augmented assignment is the combination, in a single statement, of a
binary operation and an assignment statement:

   augmented_assignment_stmt ::= augtarget augop (expression_list | yield_expression)
   augtarget                 ::= identifier | attributeref | subscription | slicing
   augop                     ::= "+=" | "-=" | "*=" | "@=" | "/=" | "//=" | "%=" | "**="
             | ">>=" | "<<=" | "&=" | "^=" | "|="

(See section Primaries for the syntax definitions of the last three
symbols.)

An augmented assignment evaluates the target (which, unlike normal
assignment statements, cannot be an unpacking) and the expression
list, performs the binary operation specific to the type of assignment
on the two operands, and assigns the result to the original target.
The target is only evaluated once.

An augmented assignment expression like "x += 1" can be rewritten as
"x = x + 1" to achieve a similar, but not exactly equal effect. In the
augmented version, "x" is only evaluated once. Also, when possible,
the actual operation is performed *in-place*, meaning that rather than
creating a new object and assigning that to the target, the old object
is modified instead.

Unlike normal assignments, augmented assignments evaluate the left-
hand side *before* evaluating the right-hand side.  For example, "a[i]
+= f(x)" first looks-up "a[i]", then it evaluates "f(x)" and performs
the addition, and lastly, it writes the result back to "a[i]".

With the exception of assigning to tuples and multiple targets in a
single statement, the assignment done by augmented assignment
statements is handled the same way as normal assignments. Similarly,
with the exception of the possible *in-place* behavior, the binary
operation performed by augmented assignment is the same as the normal
binary operations.

For targets which are attribute references, the same caveat about
class and instance attributes applies as for regular assignments.
"""
    , 'binary':
    """Binary arithmetic operations
****************************

The binary arithmetic operations have the conventional priority
levels.  Note that some of these operations also apply to certain non-
numeric types.  Apart from the power operator, there are only two
levels, one for multiplicative operators and one for additive
operators:

   m_expr ::= u_expr | m_expr "*" u_expr | m_expr "@" m_expr |
              m_expr "//" u_expr| m_expr "/" u_expr |
              m_expr "%" u_expr
   a_expr ::= m_expr | a_expr "+" m_expr | a_expr "-" m_expr

The "*" (multiplication) operator yields the product of its arguments.
The arguments must either both be numbers, or one argument must be an
integer and the other must be a sequence. In the former case, the
numbers are converted to a common type and then multiplied together.
In the latter case, sequence repetition is performed; a negative
repetition factor yields an empty sequence.

The "@" (at) operator is intended to be used for matrix
multiplication.  No builtin Python types implement this operator.

New in version 3.5.

The "/" (division) and "//" (floor division) operators yield the
quotient of their arguments.  The numeric arguments are first
converted to a common type. Division of integers yields a float, while
floor division of integers results in an integer; the result is that
of mathematical division with the 'floor' function applied to the
result.  Division by zero raises the "ZeroDivisionError" exception.

The "%" (modulo) operator yields the remainder from the division of
the first argument by the second.  The numeric arguments are first
converted to a common type.  A zero right argument raises the
"ZeroDivisionError" exception.  The arguments may be floating point
numbers, e.g., "3.14%0.7" equals "0.34" (since "3.14" equals "4*0.7 +
0.34".)  The modulo operator always yields a result with the same sign
as its second operand (or zero); the absolute value of the result is
strictly smaller than the absolute value of the second operand [1].

The floor division and modulo operators are connected by the following
identity: "x == (x//y)*y + (x%y)".  Floor division and modulo are also
connected with the built-in function "divmod()": "divmod(x, y) ==
(x//y, x%y)". [2].

In addition to performing the modulo operation on numbers, the "%"
operator is also overloaded by string objects to perform old-style
string formatting (also known as interpolation).  The syntax for
string formatting is described in the Python Library Reference,
section printf-style String Formatting.

The floor division operator, the modulo operator, and the "divmod()"
function are not defined for complex numbers.  Instead, convert to a
floating point number using the "abs()" function if appropriate.

The "+" (addition) operator yields the sum of its arguments.  The
arguments must either both be numbers or both be sequences of the same
type.  In the former case, the numbers are converted to a common type
and then added together. In the latter case, the sequences are
concatenated.

The "-" (subtraction) operator yields the difference of its arguments.
The numeric arguments are first converted to a common type.
"""
    , 'bitwise':
    """Binary bitwise operations
*************************

Each of the three bitwise operations has a different priority level:

   and_expr ::= shift_expr | and_expr "&" shift_expr
   xor_expr ::= and_expr | xor_expr "^" and_expr
   or_expr  ::= xor_expr | or_expr "|" xor_expr

The "&" operator yields the bitwise AND of its arguments, which must
be integers.

The "^" operator yields the bitwise XOR (exclusive OR) of its
arguments, which must be integers.

The "|" operator yields the bitwise (inclusive) OR of its arguments,
which must be integers.
"""
    , 'bltin-code-objects':
    """Code Objects
************

Code objects are used by the implementation to represent "pseudo-
compiled" executable Python code such as a function body. They differ
from function objects because they don't contain a reference to their
global execution environment.  Code objects are returned by the built-
in "compile()" function and can be extracted from function objects
through their "__code__" attribute. See also the "code" module.

A code object can be executed or evaluated by passing it (instead of a
source string) to the "exec()" or "eval()"  built-in functions.

See The standard type hierarchy for more information.
"""
    , 'bltin-ellipsis-object':
    """The Ellipsis Object
*******************

This object is commonly used by slicing (see Slicings).  It supports
no special operations.  There is exactly one ellipsis object, named
"Ellipsis" (a built-in name).  "type(Ellipsis)()" produces the
"Ellipsis" singleton.

It is written as "Ellipsis" or "...".
"""
    , 'bltin-null-object':
    """The Null Object
***************

This object is returned by functions that don't explicitly return a
value.  It supports no special operations.  There is exactly one null
object, named "None" (a built-in name).  "type(None)()" produces the
same singleton.

It is written as "None".
"""
    , 'bltin-type-objects':
    """Type Objects
************

Type objects represent the various object types.  An object's type is
accessed by the built-in function "type()".  There are no special
operations on types.  The standard module "types" defines names for
all standard built-in types.

Types are written like this: "<class 'int'>".
"""
    , 'booleans':
    """Boolean operations
******************

   or_test  ::= and_test | or_test "or" and_test
   and_test ::= not_test | and_test "and" not_test
   not_test ::= comparison | "not" not_test

In the context of Boolean operations, and also when expressions are
used by control flow statements, the following values are interpreted
as false: "False", "None", numeric zero of all types, and empty
strings and containers (including strings, tuples, lists,
dictionaries, sets and frozensets).  All other values are interpreted
as true.  User-defined objects can customize their truth value by
providing a "__bool__()" method.

The operator "not" yields "True" if its argument is false, "False"
otherwise.

The expression "x and y" first evaluates *x*; if *x* is false, its
value is returned; otherwise, *y* is evaluated and the resulting value
is returned.

The expression "x or y" first evaluates *x*; if *x* is true, its value
is returned; otherwise, *y* is evaluated and the resulting value is
returned.

(Note that neither "and" nor "or" restrict the value and type they
return to "False" and "True", but rather return the last evaluated
argument.  This is sometimes useful, e.g., if "s" is a string that
should be replaced by a default value if it is empty, the expression
"s or 'foo'" yields the desired value.  Because "not" has to create a
new value, it returns a boolean value regardless of the type of its
argument (for example, "not 'foo'" produces "False" rather than "''".)
"""
    , 'break':
    """The "break" statement
*********************

   break_stmt ::= "break"

"break" may only occur syntactically nested in a "for" or "while"
loop, but not nested in a function or class definition within that
loop.

It terminates the nearest enclosing loop, skipping the optional "else"
clause if the loop has one.

If a "for" loop is terminated by "break", the loop control target
keeps its current value.

When "break" passes control out of a "try" statement with a "finally"
clause, that "finally" clause is executed before really leaving the
loop.
"""
    , 'callable-types':
    """Emulating callable objects
**************************

object.__call__(self[, args...])

   Called when the instance is "called" as a function; if this method
   is defined, "x(arg1, arg2, ...)" is a shorthand for
   "x.__call__(arg1, arg2, ...)".
"""
    , 'calls':
    """Calls
*****

A call calls a callable object (e.g., a *function*) with a possibly
empty series of *arguments*:

   call                 ::= primary "(" [argument_list [","] | comprehension] ")"
   argument_list        ::= positional_arguments ["," starred_and_keywords]
                       ["," keywords_arguments]
                     | starred_and_keywords ["," keywords_arguments]
                     | keywords_arguments
   positional_arguments ::= ["*"] expression ("," ["*"] expression)*
   starred_and_keywords ::= ("*" expression | keyword_item)
                            ("," "*" expression | "," keyword_item)*
   keywords_arguments   ::= (keyword_item | "**" expression)
                          ("," keyword_item | "," "**" expression)*
   keyword_item         ::= identifier "=" expression

An optional trailing comma may be present after the positional and
keyword arguments but does not affect the semantics.

The primary must evaluate to a callable object (user-defined
functions, built-in functions, methods of built-in objects, class
objects, methods of class instances, and all objects having a
"__call__()" method are callable).  All argument expressions are
evaluated before the call is attempted.  Please refer to section
Function definitions for the syntax of formal *parameter* lists.

If keyword arguments are present, they are first converted to
positional arguments, as follows.  First, a list of unfilled slots is
created for the formal parameters.  If there are N positional
arguments, they are placed in the first N slots.  Next, for each
keyword argument, the identifier is used to determine the
corresponding slot (if the identifier is the same as the first formal
parameter name, the first slot is used, and so on).  If the slot is
already filled, a "TypeError" exception is raised. Otherwise, the
value of the argument is placed in the slot, filling it (even if the
expression is "None", it fills the slot).  When all arguments have
been processed, the slots that are still unfilled are filled with the
corresponding default value from the function definition.  (Default
values are calculated, once, when the function is defined; thus, a
mutable object such as a list or dictionary used as default value will
be shared by all calls that don't specify an argument value for the
corresponding slot; this should usually be avoided.)  If there are any
unfilled slots for which no default value is specified, a "TypeError"
exception is raised.  Otherwise, the list of filled slots is used as
the argument list for the call.

**CPython implementation detail:** An implementation may provide
built-in functions whose positional parameters do not have names, even
if they are 'named' for the purpose of documentation, and which
therefore cannot be supplied by keyword.  In CPython, this is the case
for functions implemented in C that use "PyArg_ParseTuple()" to parse
their arguments.

If there are more positional arguments than there are formal parameter
slots, a "TypeError" exception is raised, unless a formal parameter
using the syntax "*identifier" is present; in this case, that formal
parameter receives a tuple containing the excess positional arguments
(or an empty tuple if there were no excess positional arguments).

If any keyword argument does not correspond to a formal parameter
name, a "TypeError" exception is raised, unless a formal parameter
using the syntax "**identifier" is present; in this case, that formal
parameter receives a dictionary containing the excess keyword
arguments (using the keywords as keys and the argument values as
corresponding values), or a (new) empty dictionary if there were no
excess keyword arguments.

If the syntax "*expression" appears in the function call, "expression"
must evaluate to an *iterable*.  Elements from these iterables are
treated as if they were additional positional arguments.  For the call
"f(x1, x2, *y, x3, x4)", if *y* evaluates to a sequence *y1*, ...,
*yM*, this is equivalent to a call with M+4 positional arguments *x1*,
*x2*, *y1*, ..., *yM*, *x3*, *x4*.

A consequence of this is that although the "*expression" syntax may
appear *after* explicit keyword arguments, it is processed *before*
the keyword arguments (and any "**expression" arguments -- see below).
So:

   >>> def f(a, b):
   ...     print(a, b)
   ...
   >>> f(b=1, *(2,))
   2 1
   >>> f(a=1, *(2,))
   Traceback (most recent call last):
     File "<stdin>", line 1, in <module>
   TypeError: f() got multiple values for keyword argument 'a'
   >>> f(1, *(2,))
   1 2

It is unusual for both keyword arguments and the "*expression" syntax
to be used in the same call, so in practice this confusion does not
arise.

If the syntax "**expression" appears in the function call,
"expression" must evaluate to a *mapping*, the contents of which are
treated as additional keyword arguments.  If a keyword is already
present (as an explicit keyword argument, or from another unpacking),
a "TypeError" exception is raised.

Formal parameters using the syntax "*identifier" or "**identifier"
cannot be used as positional argument slots or as keyword argument
names.

Changed in version 3.5: Function calls accept any number of "*" and
"**" unpackings, positional arguments may follow iterable unpackings
("*"), and keyword arguments may follow dictionary unpackings ("**").
Originally proposed by **PEP 448**.

A call always returns some value, possibly "None", unless it raises an
exception.  How this value is computed depends on the type of the
callable object.

If it is---

a user-defined function:
   The code block for the function is executed, passing it the
   argument list.  The first thing the code block will do is bind the
   formal parameters to the arguments; this is described in section
   Function definitions.  When the code block executes a "return"
   statement, this specifies the return value of the function call.

a built-in function or method:
   The result is up to the interpreter; see Built-in Functions for the
   descriptions of built-in functions and methods.

a class object:
   A new instance of that class is returned.

a class instance method:
   The corresponding user-defined function is called, with an argument
   list that is one longer than the argument list of the call: the
   instance becomes the first argument.

a class instance:
   The class must define a "__call__()" method; the effect is then the
   same as if that method was called.
"""
    , 'class':
    """Class definitions
*****************

A class definition defines a class object (see section The standard
type hierarchy):

   classdef    ::= [decorators] "class" classname [inheritance] ":" suite
   inheritance ::= "(" [argument_list] ")"
   classname   ::= identifier

A class definition is an executable statement.  The inheritance list
usually gives a list of base classes (see Metaclasses for more
advanced uses), so each item in the list should evaluate to a class
object which allows subclassing.  Classes without an inheritance list
inherit, by default, from the base class "object"; hence,

   class Foo:
       pass

is equivalent to

   class Foo(object):
       pass

The class's suite is then executed in a new execution frame (see
Naming and binding), using a newly created local namespace and the
original global namespace. (Usually, the suite contains mostly
function definitions.)  When the class's suite finishes execution, its
execution frame is discarded but its local namespace is saved. [4] A
class object is then created using the inheritance list for the base
classes and the saved local namespace for the attribute dictionary.
The class name is bound to this class object in the original local
namespace.

The order in which attributes are defined in the class body is
preserved in the new class's "__dict__".  Note that this is reliable
only right after the class is created and only for classes that were
defined using the definition syntax.

Class creation can be customized heavily using metaclasses.

Classes can also be decorated: just like when decorating functions,

   @f1(arg)
   @f2
   class Foo: pass

is roughly equivalent to

   class Foo: pass
   Foo = f1(arg)(f2(Foo))

The evaluation rules for the decorator expressions are the same as for
function decorators.  The result is then bound to the class name.

**Programmer's note:** Variables defined in the class definition are
class attributes; they are shared by instances.  Instance attributes
can be set in a method with "self.name = value".  Both class and
instance attributes are accessible through the notation ""self.name"",
and an instance attribute hides a class attribute with the same name
when accessed in this way.  Class attributes can be used as defaults
for instance attributes, but using mutable values there can lead to
unexpected results.  Descriptors can be used to create instance
variables with different implementation details.

See also: **PEP 3115** - Metaclasses in Python 3 **PEP 3129** -
  Class Decorators
"""
    , 'comparisons':
    """Comparisons
***********

Unlike C, all comparison operations in Python have the same priority,
which is lower than that of any arithmetic, shifting or bitwise
operation.  Also unlike C, expressions like "a < b < c" have the
interpretation that is conventional in mathematics:

   comparison    ::= or_expr ( comp_operator or_expr )*
   comp_operator ::= "<" | ">" | "==" | ">=" | "<=" | "!="
                     | "is" ["not"] | ["not"] "in"

Comparisons yield boolean values: "True" or "False".

Comparisons can be chained arbitrarily, e.g., "x < y <= z" is
equivalent to "x < y and y <= z", except that "y" is evaluated only
once (but in both cases "z" is not evaluated at all when "x < y" is
found to be false).

Formally, if *a*, *b*, *c*, ..., *y*, *z* are expressions and *op1*,
*op2*, ..., *opN* are comparison operators, then "a op1 b op2 c ... y
opN z" is equivalent to "a op1 b and b op2 c and ... y opN z", except
that each expression is evaluated at most once.

Note that "a op1 b op2 c" doesn't imply any kind of comparison between
*a* and *c*, so that, e.g., "x < y > z" is perfectly legal (though
perhaps not pretty).


Value comparisons
=================

The operators "<", ">", "==", ">=", "<=", and "!=" compare the values
of two objects.  The objects do not need to have the same type.

Chapter Objects, values and types states that objects have a value (in
addition to type and identity).  The value of an object is a rather
abstract notion in Python: For example, there is no canonical access
method for an object's value.  Also, there is no requirement that the
value of an object should be constructed in a particular way, e.g.
comprised of all its data attributes. Comparison operators implement a
particular notion of what the value of an object is.  One can think of
them as defining the value of an object indirectly, by means of their
comparison implementation.

Because all types are (direct or indirect) subtypes of "object", they
inherit the default comparison behavior from "object".  Types can
customize their comparison behavior by implementing *rich comparison
methods* like "__lt__()", described in Basic customization.

The default behavior for equality comparison ("==" and "!=") is based
on the identity of the objects.  Hence, equality comparison of
instances with the same identity results in equality, and equality
comparison of instances with different identities results in
inequality.  A motivation for this default behavior is the desire that
all objects should be reflexive (i.e. "x is y" implies "x == y").

A default order comparison ("<", ">", "<=", and ">=") is not provided;
an attempt raises "TypeError".  A motivation for this default behavior
is the lack of a similar invariant as for equality.

The behavior of the default equality comparison, that instances with
different identities are always unequal, may be in contrast to what
types will need that have a sensible definition of object value and
value-based equality.  Such types will need to customize their
comparison behavior, and in fact, a number of built-in types have done
that.

The following list describes the comparison behavior of the most
important built-in types.

* Numbers of built-in numeric types (Numeric Types --- int, float,
  complex) and of the standard library types "fractions.Fraction" and
  "decimal.Decimal" can be compared within and across their types,
  with the restriction that complex numbers do not support order
  comparison.  Within the limits of the types involved, they compare
  mathematically (algorithmically) correct without loss of precision.

  The not-a-number values "float('NaN')" and "Decimal('NaN')" are
  special.  They are identical to themselves ("x is x" is true) but
  are not equal to themselves ("x == x" is false).  Additionally,
  comparing any number to a not-a-number value will return "False".
  For example, both "3 < float('NaN')" and "float('NaN') < 3" will
  return "False".

* Binary sequences (instances of "bytes" or "bytearray") can be
  compared within and across their types.  They compare
  lexicographically using the numeric values of their elements.

* Strings (instances of "str") compare lexicographically using the
  numerical Unicode code points (the result of the built-in function
  "ord()") of their characters. [3]

  Strings and binary sequences cannot be directly compared.

* Sequences (instances of "tuple", "list", or "range") can be
  compared only within each of their types, with the restriction that
  ranges do not support order comparison.  Equality comparison across
  these types results in inequality, and ordering comparison across
  these types raises "TypeError".

  Sequences compare lexicographically using comparison of
  corresponding elements, whereby reflexivity of the elements is
  enforced.

  In enforcing reflexivity of elements, the comparison of collections
  assumes that for a collection element "x", "x == x" is always true.
  Based on that assumption, element identity is compared first, and
  element comparison is performed only for distinct elements.  This
  approach yields the same result as a strict element comparison
  would, if the compared elements are reflexive.  For non-reflexive
  elements, the result is different than for strict element
  comparison, and may be surprising:  The non-reflexive not-a-number
  values for example result in the following comparison behavior when
  used in a list:

     >>> nan = float('NaN')
     >>> nan is nan
     True
     >>> nan == nan
     False                 <-- the defined non-reflexive behavior of NaN
     >>> [nan] == [nan]
     True                  <-- list enforces reflexivity and tests identity first

  Lexicographical comparison between built-in collections works as
  follows:

  * For two collections to compare equal, they must be of the same
    type, have the same length, and each pair of corresponding
    elements must compare equal (for example, "[1,2] == (1,2)" is
    false because the type is not the same).

  * Collections that support order comparison are ordered the same
    as their first unequal elements (for example, "[1,2,x] <= [1,2,y]"
    has the same value as "x <= y").  If a corresponding element does
    not exist, the shorter collection is ordered first (for example,
    "[1,2] < [1,2,3]" is true).

* Mappings (instances of "dict") compare equal if and only if they
  have equal *(key, value)* pairs. Equality comparison of the keys and
  values enforces reflexivity.

  Order comparisons ("<", ">", "<=", and ">=") raise "TypeError".

* Sets (instances of "set" or "frozenset") can be compared within
  and across their types.

  They define order comparison operators to mean subset and superset
  tests.  Those relations do not define total orderings (for example,
  the two sets "{1,2}" and "{2,3}" are not equal, nor subsets of one
  another, nor supersets of one another).  Accordingly, sets are not
  appropriate arguments for functions which depend on total ordering
  (for example, "min()", "max()", and "sorted()" produce undefined
  results given a list of sets as inputs).

  Comparison of sets enforces reflexivity of its elements.

* Most other built-in types have no comparison methods implemented,
  so they inherit the default comparison behavior.

User-defined classes that customize their comparison behavior should
follow some consistency rules, if possible:

* Equality comparison should be reflexive. In other words, identical
  objects should compare equal:

     "x is y" implies "x == y"

* Comparison should be symmetric. In other words, the following
  expressions should have the same result:

     "x == y" and "y == x"

     "x != y" and "y != x"

     "x < y" and "y > x"

     "x <= y" and "y >= x"

* Comparison should be transitive. The following (non-exhaustive)
  examples illustrate that:

     "x > y and y > z" implies "x > z"

     "x < y and y <= z" implies "x < z"

* Inverse comparison should result in the boolean negation. In other
  words, the following expressions should have the same result:

     "x == y" and "not x != y"

     "x < y" and "not x >= y" (for total ordering)

     "x > y" and "not x <= y" (for total ordering)

  The last two expressions apply to totally ordered collections (e.g.
  to sequences, but not to sets or mappings). See also the
  "total_ordering()" decorator.

* The "hash()" result should be consistent with equality. Objects
  that are equal should either have the same hash value, or be marked
  as unhashable.

Python does not enforce these consistency rules. In fact, the
not-a-number values are an example for not following these rules.


Membership test operations
==========================

The operators "in" and "not in" test for membership.  "x in s"
evaluates to "True" if *x* is a member of *s*, and "False" otherwise.
"x not in s" returns the negation of "x in s".  All built-in sequences
and set types support this as well as dictionary, for which "in" tests
whether the dictionary has a given key. For container types such as
list, tuple, set, frozenset, dict, or collections.deque, the
expression "x in y" is equivalent to "any(x is e or x == e for e in
y)".

For the string and bytes types, "x in y" is "True" if and only if *x*
is a substring of *y*.  An equivalent test is "y.find(x) != -1".
Empty strings are always considered to be a substring of any other
string, so ""\" in "abc"" will return "True".

For user-defined classes which define the "__contains__()" method, "x
in y" returns "True" if "y.__contains__(x)" returns a true value, and
"False" otherwise.

For user-defined classes which do not define "__contains__()" but do
define "__iter__()", "x in y" is "True" if some value "z" with "x ==
z" is produced while iterating over "y".  If an exception is raised
during the iteration, it is as if "in" raised that exception.

Lastly, the old-style iteration protocol is tried: if a class defines
"__getitem__()", "x in y" is "True" if and only if there is a non-
negative integer index *i* such that "x == y[i]", and all lower
integer indices do not raise "IndexError" exception.  (If any other
exception is raised, it is as if "in" raised that exception).

The operator "not in" is defined to have the inverse true value of
"in".


Identity comparisons
====================

The operators "is" and "is not" test for object identity: "x is y" is
true if and only if *x* and *y* are the same object.  Object identity
is determined using the "id()" function.  "x is not y" yields the
inverse truth value. [4]
"""
    , 'compound':
    """Compound statements
*******************

Compound statements contain (groups of) other statements; they affect
or control the execution of those other statements in some way.  In
general, compound statements span multiple lines, although in simple
incarnations a whole compound statement may be contained in one line.

The "if", "while" and "for" statements implement traditional control
flow constructs.  "try" specifies exception handlers and/or cleanup
code for a group of statements, while the "with" statement allows the
execution of initialization and finalization code around a block of
code.  Function and class definitions are also syntactically compound
statements.

A compound statement consists of one or more 'clauses.'  A clause
consists of a header and a 'suite.'  The clause headers of a
particular compound statement are all at the same indentation level.
Each clause header begins with a uniquely identifying keyword and ends
with a colon.  A suite is a group of statements controlled by a
clause.  A suite can be one or more semicolon-separated simple
statements on the same line as the header, following the header's
colon, or it can be one or more indented statements on subsequent
lines.  Only the latter form of a suite can contain nested compound
statements; the following is illegal, mostly because it wouldn't be
clear to which "if" clause a following "else" clause would belong:

   if test1: if test2: print(x)

Also note that the semicolon binds tighter than the colon in this
context, so that in the following example, either all or none of the
"print()" calls are executed:

   if x < y < z: print(x); print(y); print(z)

Summarizing:

   compound_stmt ::= if_stmt
                     | while_stmt
                     | for_stmt
                     | try_stmt
                     | with_stmt
                     | funcdef
                     | classdef
                     | async_with_stmt
                     | async_for_stmt
                     | async_funcdef
   suite         ::= stmt_list NEWLINE | NEWLINE INDENT statement+ DEDENT
   statement     ::= stmt_list NEWLINE | compound_stmt
   stmt_list     ::= simple_stmt (";" simple_stmt)* [";"]

Note that statements always end in a "NEWLINE" possibly followed by a
"DEDENT".  Also note that optional continuation clauses always begin
with a keyword that cannot start a statement, thus there are no
ambiguities (the 'dangling "else"' problem is solved in Python by
requiring nested "if" statements to be indented).

The formatting of the grammar rules in the following sections places
each clause on a separate line for clarity.


The "if" statement
==================

The "if" statement is used for conditional execution:

   if_stmt ::= "if" expression ":" suite
               ( "elif" expression ":" suite )*
               ["else" ":" suite]

It selects exactly one of the suites by evaluating the expressions one
by one until one is found to be true (see section Boolean operations
for the definition of true and false); then that suite is executed
(and no other part of the "if" statement is executed or evaluated).
If all expressions are false, the suite of the "else" clause, if
present, is executed.


The "while" statement
=====================

The "while" statement is used for repeated execution as long as an
expression is true:

   while_stmt ::= "while" expression ":" suite
                  ["else" ":" suite]

This repeatedly tests the expression and, if it is true, executes the
first suite; if the expression is false (which may be the first time
it is tested) the suite of the "else" clause, if present, is executed
and the loop terminates.

A "break" statement executed in the first suite terminates the loop
without executing the "else" clause's suite.  A "continue" statement
executed in the first suite skips the rest of the suite and goes back
to testing the expression.


The "for" statement
===================

The "for" statement is used to iterate over the elements of a sequence
(such as a string, tuple or list) or other iterable object:

   for_stmt ::= "for" target_list "in" expression_list ":" suite
                ["else" ":" suite]

The expression list is evaluated once; it should yield an iterable
object.  An iterator is created for the result of the
"expression_list".  The suite is then executed once for each item
provided by the iterator, in the order returned by the iterator.  Each
item in turn is assigned to the target list using the standard rules
for assignments (see Assignment statements), and then the suite is
executed.  When the items are exhausted (which is immediately when the
sequence is empty or an iterator raises a "StopIteration" exception),
the suite in the "else" clause, if present, is executed, and the loop
terminates.

A "break" statement executed in the first suite terminates the loop
without executing the "else" clause's suite.  A "continue" statement
executed in the first suite skips the rest of the suite and continues
with the next item, or with the "else" clause if there is no next
item.

The for-loop makes assignments to the variables(s) in the target list.
This overwrites all previous assignments to those variables including
those made in the suite of the for-loop:

   for i in range(10):
       print(i)
       i = 5             # this will not affect the for-loop
                         # because i will be overwritten with the next
                         # index in the range

Names in the target list are not deleted when the loop is finished,
but if the sequence is empty, they will not have been assigned to at
all by the loop.  Hint: the built-in function "range()" returns an
iterator of integers suitable to emulate the effect of Pascal's "for i
:= a to b do"; e.g., "list(range(3))" returns the list "[0, 1, 2]".

Note: There is a subtlety when the sequence is being modified by the
  loop (this can only occur for mutable sequences, i.e. lists).  An
  internal counter is used to keep track of which item is used next,
  and this is incremented on each iteration.  When this counter has
  reached the length of the sequence the loop terminates.  This means
  that if the suite deletes the current (or a previous) item from the
  sequence, the next item will be skipped (since it gets the index of
  the current item which has already been treated).  Likewise, if the
  suite inserts an item in the sequence before the current item, the
  current item will be treated again the next time through the loop.
  This can lead to nasty bugs that can be avoided by making a
  temporary copy using a slice of the whole sequence, e.g.,

     for x in a[:]:
         if x < 0: a.remove(x)


The "try" statement
===================

The "try" statement specifies exception handlers and/or cleanup code
for a group of statements:

   try_stmt  ::= try1_stmt | try2_stmt
   try1_stmt ::= "try" ":" suite
                 ("except" [expression ["as" identifier]] ":" suite)+
                 ["else" ":" suite]
                 ["finally" ":" suite]
   try2_stmt ::= "try" ":" suite
                 "finally" ":" suite

The "except" clause(s) specify one or more exception handlers. When no
exception occurs in the "try" clause, no exception handler is
executed. When an exception occurs in the "try" suite, a search for an
exception handler is started.  This search inspects the except clauses
in turn until one is found that matches the exception.  An expression-
less except clause, if present, must be last; it matches any
exception.  For an except clause with an expression, that expression
is evaluated, and the clause matches the exception if the resulting
object is "compatible" with the exception.  An object is compatible
with an exception if it is the class or a base class of the exception
object or a tuple containing an item compatible with the exception.

If no except clause matches the exception, the search for an exception
handler continues in the surrounding code and on the invocation stack.
[1]

If the evaluation of an expression in the header of an except clause
raises an exception, the original search for a handler is canceled and
a search starts for the new exception in the surrounding code and on
the call stack (it is treated as if the entire "try" statement raised
the exception).

When a matching except clause is found, the exception is assigned to
the target specified after the "as" keyword in that except clause, if
present, and the except clause's suite is executed.  All except
clauses must have an executable block.  When the end of this block is
reached, execution continues normally after the entire try statement.
(This means that if two nested handlers exist for the same exception,
and the exception occurs in the try clause of the inner handler, the
outer handler will not handle the exception.)

When an exception has been assigned using "as target", it is cleared
at the end of the except clause.  This is as if

   except E as N:
       foo

was translated to

   except E as N:
       try:
           foo
       finally:
           del N

This means the exception must be assigned to a different name to be
able to refer to it after the except clause.  Exceptions are cleared
because with the traceback attached to them, they form a reference
cycle with the stack frame, keeping all locals in that frame alive
until the next garbage collection occurs.

Before an except clause's suite is executed, details about the
exception are stored in the "sys" module and can be accessed via
"sys.exc_info()". "sys.exc_info()" returns a 3-tuple consisting of the
exception class, the exception instance and a traceback object (see
section The standard type hierarchy) identifying the point in the
program where the exception occurred.  "sys.exc_info()" values are
restored to their previous values (before the call) when returning
from a function that handled an exception.

The optional "else" clause is executed if and when control flows off
the end of the "try" clause. [2] Exceptions in the "else" clause are
not handled by the preceding "except" clauses.

If "finally" is present, it specifies a 'cleanup' handler.  The "try"
clause is executed, including any "except" and "else" clauses.  If an
exception occurs in any of the clauses and is not handled, the
exception is temporarily saved. The "finally" clause is executed.  If
there is a saved exception it is re-raised at the end of the "finally"
clause.  If the "finally" clause raises another exception, the saved
exception is set as the context of the new exception. If the "finally"
clause executes a "return" or "break" statement, the saved exception
is discarded:

   >>> def f():
   ...     try:
   ...         1/0
   ...     finally:
   ...         return 42
   ...
   >>> f()
   42

The exception information is not available to the program during
execution of the "finally" clause.

When a "return", "break" or "continue" statement is executed in the
"try" suite of a "try"..."finally" statement, the "finally" clause is
also executed 'on the way out.' A "continue" statement is illegal in
the "finally" clause. (The reason is a problem with the current
implementation --- this restriction may be lifted in the future).

The return value of a function is determined by the last "return"
statement executed.  Since the "finally" clause always executes, a
"return" statement executed in the "finally" clause will always be the
last one executed:

   >>> def foo():
   ...     try:
   ...         return 'try'
   ...     finally:
   ...         return 'finally'
   ...
   >>> foo()
   'finally'

Additional information on exceptions can be found in section
Exceptions, and information on using the "raise" statement to generate
exceptions may be found in section The raise statement.


The "with" statement
====================

The "with" statement is used to wrap the execution of a block with
methods defined by a context manager (see section With Statement
Context Managers). This allows common "try"..."except"..."finally"
usage patterns to be encapsulated for convenient reuse.

   with_stmt ::= "with" with_item ("," with_item)* ":" suite
   with_item ::= expression ["as" target]

The execution of the "with" statement with one "item" proceeds as
follows:

1. The context expression (the expression given in the "with_item")
   is evaluated to obtain a context manager.

2. The context manager's "__exit__()" is loaded for later use.

3. The context manager's "__enter__()" method is invoked.

4. If a target was included in the "with" statement, the return
   value from "__enter__()" is assigned to it.

   Note: The "with" statement guarantees that if the "__enter__()"
     method returns without an error, then "__exit__()" will always be
     called. Thus, if an error occurs during the assignment to the
     target list, it will be treated the same as an error occurring
     within the suite would be. See step 6 below.

5. The suite is executed.

6. The context manager's "__exit__()" method is invoked.  If an
   exception caused the suite to be exited, its type, value, and
   traceback are passed as arguments to "__exit__()". Otherwise, three
   "None" arguments are supplied.

   If the suite was exited due to an exception, and the return value
   from the "__exit__()" method was false, the exception is reraised.
   If the return value was true, the exception is suppressed, and
   execution continues with the statement following the "with"
   statement.

   If the suite was exited for any reason other than an exception, the
   return value from "__exit__()" is ignored, and execution proceeds
   at the normal location for the kind of exit that was taken.

With more than one item, the context managers are processed as if
multiple "with" statements were nested:

   with A() as a, B() as b:
       suite

is equivalent to

   with A() as a:
       with B() as b:
           suite

Changed in version 3.1: Support for multiple context expressions.

See also:

  **PEP 343** - The "with" statement
     The specification, background, and examples for the Python "with"
     statement.


Function definitions
====================

A function definition defines a user-defined function object (see
section The standard type hierarchy):

   funcdef                 ::= [decorators] "def" funcname "(" [parameter_list] ")" ["->" expression] ":" suite
   decorators              ::= decorator+
   decorator               ::= "@" dotted_name ["(" [argument_list [","]] ")"] NEWLINE
   dotted_name             ::= identifier ("." identifier)*
   parameter_list          ::= defparameter ("," defparameter)* ["," [parameter_list_starargs]]
                      | parameter_list_starargs
   parameter_list_starargs ::= "*" [parameter] ("," defparameter)* ["," ["**" parameter [","]]]
                               | "**" parameter [","]
   parameter               ::= identifier [":" expression]
   defparameter            ::= parameter ["=" expression]
   funcname                ::= identifier

A function definition is an executable statement.  Its execution binds
the function name in the current local namespace to a function object
(a wrapper around the executable code for the function).  This
function object contains a reference to the current global namespace
as the global namespace to be used when the function is called.

The function definition does not execute the function body; this gets
executed only when the function is called. [3]

A function definition may be wrapped by one or more *decorator*
expressions. Decorator expressions are evaluated when the function is
defined, in the scope that contains the function definition.  The
result must be a callable, which is invoked with the function object
as the only argument. The returned value is bound to the function name
instead of the function object.  Multiple decorators are applied in
nested fashion. For example, the following code

   @f1(arg)
   @f2
   def func(): pass

is roughly equivalent to

   def func(): pass
   func = f1(arg)(f2(func))

except that the original function is not temporarily bound to the name
"func".

When one or more *parameters* have the form *parameter* "="
*expression*, the function is said to have "default parameter values."
For a parameter with a default value, the corresponding *argument* may
be omitted from a call, in which case the parameter's default value is
substituted.  If a parameter has a default value, all following
parameters up until the ""*"" must also have a default value --- this
is a syntactic restriction that is not expressed by the grammar.

**Default parameter values are evaluated from left to right when the
function definition is executed.** This means that the expression is
evaluated once, when the function is defined, and that the same "pre-
computed" value is used for each call.  This is especially important
to understand when a default parameter is a mutable object, such as a
list or a dictionary: if the function modifies the object (e.g. by
appending an item to a list), the default value is in effect modified.
This is generally not what was intended.  A way around this is to use
"None" as the default, and explicitly test for it in the body of the
function, e.g.:

   def whats_on_the_telly(penguin=None):
       if penguin is None:
           penguin = []
       penguin.append("property of the zoo")
       return penguin

Function call semantics are described in more detail in section Calls.
A function call always assigns values to all parameters mentioned in
the parameter list, either from position arguments, from keyword
arguments, or from default values.  If the form ""*identifier"" is
present, it is initialized to a tuple receiving any excess positional
parameters, defaulting to the empty tuple. If the form
""**identifier"" is present, it is initialized to a new ordered
mapping receiving any excess keyword arguments, defaulting to a new
empty mapping of the same type.  Parameters after ""*"" or
""*identifier"" are keyword-only parameters and may only be passed
used keyword arguments.

Parameters may have annotations of the form "": expression"" following
the parameter name.  Any parameter may have an annotation even those
of the form "*identifier" or "**identifier".  Functions may have
"return" annotation of the form ""-> expression"" after the parameter
list.  These annotations can be any valid Python expression and are
evaluated when the function definition is executed.  Annotations may
be evaluated in a different order than they appear in the source code.
The presence of annotations does not change the semantics of a
function.  The annotation values are available as values of a
dictionary keyed by the parameters' names in the "__annotations__"
attribute of the function object.

It is also possible to create anonymous functions (functions not bound
to a name), for immediate use in expressions.  This uses lambda
expressions, described in section Lambdas.  Note that the lambda
expression is merely a shorthand for a simplified function definition;
a function defined in a ""def"" statement can be passed around or
assigned to another name just like a function defined by a lambda
expression.  The ""def"" form is actually more powerful since it
allows the execution of multiple statements and annotations.

**Programmer's note:** Functions are first-class objects.  A ""def""
statement executed inside a function definition defines a local
function that can be returned or passed around.  Free variables used
in the nested function can access the local variables of the function
containing the def.  See section Naming and binding for details.

See also:

  **PEP 3107** - Function Annotations
     The original specification for function annotations.


Class definitions
=================

A class definition defines a class object (see section The standard
type hierarchy):

   classdef    ::= [decorators] "class" classname [inheritance] ":" suite
   inheritance ::= "(" [argument_list] ")"
   classname   ::= identifier

A class definition is an executable statement.  The inheritance list
usually gives a list of base classes (see Metaclasses for more
advanced uses), so each item in the list should evaluate to a class
object which allows subclassing.  Classes without an inheritance list
inherit, by default, from the base class "object"; hence,

   class Foo:
       pass

is equivalent to

   class Foo(object):
       pass

The class's suite is then executed in a new execution frame (see
Naming and binding), using a newly created local namespace and the
original global namespace. (Usually, the suite contains mostly
function definitions.)  When the class's suite finishes execution, its
execution frame is discarded but its local namespace is saved. [4] A
class object is then created using the inheritance list for the base
classes and the saved local namespace for the attribute dictionary.
The class name is bound to this class object in the original local
namespace.

The order in which attributes are defined in the class body is
preserved in the new class's "__dict__".  Note that this is reliable
only right after the class is created and only for classes that were
defined using the definition syntax.

Class creation can be customized heavily using metaclasses.

Classes can also be decorated: just like when decorating functions,

   @f1(arg)
   @f2
   class Foo: pass

is roughly equivalent to

   class Foo: pass
   Foo = f1(arg)(f2(Foo))

The evaluation rules for the decorator expressions are the same as for
function decorators.  The result is then bound to the class name.

**Programmer's note:** Variables defined in the class definition are
class attributes; they are shared by instances.  Instance attributes
can be set in a method with "self.name = value".  Both class and
instance attributes are accessible through the notation ""self.name"",
and an instance attribute hides a class attribute with the same name
when accessed in this way.  Class attributes can be used as defaults
for instance attributes, but using mutable values there can lead to
unexpected results.  Descriptors can be used to create instance
variables with different implementation details.

See also: **PEP 3115** - Metaclasses in Python 3 **PEP 3129** -
  Class Decorators


Coroutines
==========

New in version 3.5.


Coroutine function definition
-----------------------------

   async_funcdef ::= [decorators] "async" "def" funcname "(" [parameter_list] ")" ["->" expression] ":" suite

Execution of Python coroutines can be suspended and resumed at many
points (see *coroutine*).  In the body of a coroutine, any "await" and
"async" identifiers become reserved keywords; "await" expressions,
"async for" and "async with" can only be used in coroutine bodies.

Functions defined with "async def" syntax are always coroutine
functions, even if they do not contain "await" or "async" keywords.

It is a "SyntaxError" to use "yield from" expressions in "async def"
coroutines.

An example of a coroutine function:

   async def func(param1, param2):
       do_stuff()
       await some_coroutine()


The "async for" statement
-------------------------

   async_for_stmt ::= "async" for_stmt

An *asynchronous iterable* is able to call asynchronous code in its
*iter* implementation, and *asynchronous iterator* can call
asynchronous code in its *next* method.

The "async for" statement allows convenient iteration over
asynchronous iterators.

The following code:

   async for TARGET in ITER:
       BLOCK
   else:
       BLOCK2

Is semantically equivalent to:

   iter = (ITER)
   iter = type(iter).__aiter__(iter)
   running = True
   while running:
       try:
           TARGET = await type(iter).__anext__(iter)
       except StopAsyncIteration:
           running = False
       else:
           BLOCK
   else:
       BLOCK2

See also "__aiter__()" and "__anext__()" for details.

It is a "SyntaxError" to use "async for" statement outside of an
"async def" function.


The "async with" statement
--------------------------

   async_with_stmt ::= "async" with_stmt

An *asynchronous context manager* is a *context manager* that is able
to suspend execution in its *enter* and *exit* methods.

The following code:

   async with EXPR as VAR:
       BLOCK

Is semantically equivalent to:

   mgr = (EXPR)
   aexit = type(mgr).__aexit__
   aenter = type(mgr).__aenter__(mgr)
   exc = True

   VAR = await aenter
   try:
       BLOCK
   except:
       if not await aexit(mgr, *sys.exc_info()):
           raise
   else:
       await aexit(mgr, None, None, None)

See also "__aenter__()" and "__aexit__()" for details.

It is a "SyntaxError" to use "async with" statement outside of an
"async def" function.

See also: **PEP 492** - Coroutines with async and await syntax

-[ Footnotes ]-

[1] The exception is propagated to the invocation stack unless
    there is a "finally" clause which happens to raise another
    exception. That new exception causes the old one to be lost.

[2] Currently, control "flows off the end" except in the case of
    an exception or the execution of a "return", "continue", or
    "break" statement.

[3] A string literal appearing as the first statement in the
    function body is transformed into the function's "__doc__"
    attribute and therefore the function's *docstring*.

[4] A string literal appearing as the first statement in the class
    body is transformed into the namespace's "__doc__" item and
    therefore the class's *docstring*.
"""
    , 'context-managers':
    """With Statement Context Managers
*******************************

A *context manager* is an object that defines the runtime context to
be established when executing a "with" statement. The context manager
handles the entry into, and the exit from, the desired runtime context
for the execution of the block of code.  Context managers are normally
invoked using the "with" statement (described in section The with
statement), but can also be used by directly invoking their methods.

Typical uses of context managers include saving and restoring various
kinds of global state, locking and unlocking resources, closing opened
files, etc.

For more information on context managers, see Context Manager Types.

object.__enter__(self)

   Enter the runtime context related to this object. The "with"
   statement will bind this method's return value to the target(s)
   specified in the "as" clause of the statement, if any.

object.__exit__(self, exc_type, exc_value, traceback)

   Exit the runtime context related to this object. The parameters
   describe the exception that caused the context to be exited. If the
   context was exited without an exception, all three arguments will
   be "None".

   If an exception is supplied, and the method wishes to suppress the
   exception (i.e., prevent it from being propagated), it should
   return a true value. Otherwise, the exception will be processed
   normally upon exit from this method.

   Note that "__exit__()" methods should not reraise the passed-in
   exception; this is the caller's responsibility.

See also:

  **PEP 343** - The "with" statement
     The specification, background, and examples for the Python "with"
     statement.
"""
    , 'continue':
    """The "continue" statement
************************

   continue_stmt ::= "continue"

"continue" may only occur syntactically nested in a "for" or "while"
loop, but not nested in a function or class definition or "finally"
clause within that loop.  It continues with the next cycle of the
nearest enclosing loop.

When "continue" passes control out of a "try" statement with a
"finally" clause, that "finally" clause is executed before really
starting the next loop cycle.
"""
    , 'conversions':
    """Arithmetic conversions
**********************

When a description of an arithmetic operator below uses the phrase
"the numeric arguments are converted to a common type," this means
that the operator implementation for built-in types works as follows:

* If either argument is a complex number, the other is converted to
  complex;

* otherwise, if either argument is a floating point number, the
  other is converted to floating point;

* otherwise, both must be integers and no conversion is necessary.

Some additional rules apply for certain operators (e.g., a string as a
left argument to the '%' operator).  Extensions must define their own
conversion behavior.
"""
    , 'customization':
    """Basic customization
*******************

object.__new__(cls[, ...])

   Called to create a new instance of class *cls*.  "__new__()" is a
   static method (special-cased so you need not declare it as such)
   that takes the class of which an instance was requested as its
   first argument.  The remaining arguments are those passed to the
   object constructor expression (the call to the class).  The return
   value of "__new__()" should be the new object instance (usually an
   instance of *cls*).

   Typical implementations create a new instance of the class by
   invoking the superclass's "__new__()" method using
   "super().__new__(cls[, ...])" with appropriate arguments and then
   modifying the newly-created instance as necessary before returning
   it.

   If "__new__()" returns an instance of *cls*, then the new
   instance's "__init__()" method will be invoked like
   "__init__(self[, ...])", where *self* is the new instance and the
   remaining arguments are the same as were passed to "__new__()".

   If "__new__()" does not return an instance of *cls*, then the new
   instance's "__init__()" method will not be invoked.

   "__new__()" is intended mainly to allow subclasses of immutable
   types (like int, str, or tuple) to customize instance creation.  It
   is also commonly overridden in custom metaclasses in order to
   customize class creation.

object.__init__(self[, ...])

   Called after the instance has been created (by "__new__()"), but
   before it is returned to the caller.  The arguments are those
   passed to the class constructor expression.  If a base class has an
   "__init__()" method, the derived class's "__init__()" method, if
   any, must explicitly call it to ensure proper initialization of the
   base class part of the instance; for example:
   "super().__init__([args...])".

   Because "__new__()" and "__init__()" work together in constructing
   objects ("__new__()" to create it, and "__init__()" to customize
   it), no non-"None" value may be returned by "__init__()"; doing so
   will cause a "TypeError" to be raised at runtime.

object.__del__(self)

   Called when the instance is about to be destroyed.  This is also
   called a destructor.  If a base class has a "__del__()" method, the
   derived class's "__del__()" method, if any, must explicitly call it
   to ensure proper deletion of the base class part of the instance.
   Note that it is possible (though not recommended!) for the
   "__del__()" method to postpone destruction of the instance by
   creating a new reference to it.  It may then be called at a later
   time when this new reference is deleted.  It is not guaranteed that
   "__del__()" methods are called for objects that still exist when
   the interpreter exits.

   Note: "del x" doesn't directly call "x.__del__()" --- the former
     decrements the reference count for "x" by one, and the latter is
     only called when "x"'s reference count reaches zero.  Some common
     situations that may prevent the reference count of an object from
     going to zero include: circular references between objects (e.g.,
     a doubly-linked list or a tree data structure with parent and
     child pointers); a reference to the object on the stack frame of
     a function that caught an exception (the traceback stored in
     "sys.exc_info()[2]" keeps the stack frame alive); or a reference
     to the object on the stack frame that raised an unhandled
     exception in interactive mode (the traceback stored in
     "sys.last_traceback" keeps the stack frame alive).  The first
     situation can only be remedied by explicitly breaking the cycles;
     the second can be resolved by freeing the reference to the
     traceback object when it is no longer useful, and the third can
     be resolved by storing "None" in "sys.last_traceback". Circular
     references which are garbage are detected and cleaned up when the
     cyclic garbage collector is enabled (it's on by default). Refer
     to the documentation for the "gc" module for more information
     about this topic.

   Warning: Due to the precarious circumstances under which
     "__del__()" methods are invoked, exceptions that occur during
     their execution are ignored, and a warning is printed to
     "sys.stderr" instead. Also, when "__del__()" is invoked in
     response to a module being deleted (e.g., when execution of the
     program is done), other globals referenced by the "__del__()"
     method may already have been deleted or in the process of being
     torn down (e.g. the import machinery shutting down).  For this
     reason, "__del__()" methods should do the absolute minimum needed
     to maintain external invariants.  Starting with version 1.5,
     Python guarantees that globals whose name begins with a single
     underscore are deleted from their module before other globals are
     deleted; if no other references to such globals exist, this may
     help in assuring that imported modules are still available at the
     time when the "__del__()" method is called.

object.__repr__(self)

   Called by the "repr()" built-in function to compute the "official"
   string representation of an object.  If at all possible, this
   should look like a valid Python expression that could be used to
   recreate an object with the same value (given an appropriate
   environment).  If this is not possible, a string of the form
   "<...some useful description...>" should be returned. The return
   value must be a string object. If a class defines "__repr__()" but
   not "__str__()", then "__repr__()" is also used when an "informal"
   string representation of instances of that class is required.

   This is typically used for debugging, so it is important that the
   representation is information-rich and unambiguous.

object.__str__(self)

   Called by "str(object)" and the built-in functions "format()" and
   "print()" to compute the "informal" or nicely printable string
   representation of an object.  The return value must be a string
   object.

   This method differs from "object.__repr__()" in that there is no
   expectation that "__str__()" return a valid Python expression: a
   more convenient or concise representation can be used.

   The default implementation defined by the built-in type "object"
   calls "object.__repr__()".

object.__bytes__(self)

   Called by bytes to compute a byte-string representation of an
   object. This should return a "bytes" object.

object.__format__(self, format_spec)

   Called by the "format()" built-in function, and by extension,
   evaluation of formatted string literals and the "str.format()"
   method, to produce a "formatted" string representation of an
   object. The "format_spec" argument is a string that contains a
   description of the formatting options desired. The interpretation
   of the "format_spec" argument is up to the type implementing
   "__format__()", however most classes will either delegate
   formatting to one of the built-in types, or use a similar
   formatting option syntax.

   See Format Specification Mini-Language for a description of the
   standard formatting syntax.

   The return value must be a string object.

   Changed in version 3.4: The __format__ method of "object" itself
   raises a "TypeError" if passed any non-empty string.

object.__lt__(self, other)
object.__le__(self, other)
object.__eq__(self, other)
object.__ne__(self, other)
object.__gt__(self, other)
object.__ge__(self, other)

   These are the so-called "rich comparison" methods. The
   correspondence between operator symbols and method names is as
   follows: "x<y" calls "x.__lt__(y)", "x<=y" calls "x.__le__(y)",
   "x==y" calls "x.__eq__(y)", "x!=y" calls "x.__ne__(y)", "x>y" calls
   "x.__gt__(y)", and "x>=y" calls "x.__ge__(y)".

   A rich comparison method may return the singleton "NotImplemented"
   if it does not implement the operation for a given pair of
   arguments. By convention, "False" and "True" are returned for a
   successful comparison. However, these methods can return any value,
   so if the comparison operator is used in a Boolean context (e.g.,
   in the condition of an "if" statement), Python will call "bool()"
   on the value to determine if the result is true or false.

   By default, "__ne__()" delegates to "__eq__()" and inverts the
   result unless it is "NotImplemented".  There are no other implied
   relationships among the comparison operators, for example, the
   truth of "(x<y or x==y)" does not imply "x<=y". To automatically
   generate ordering operations from a single root operation, see
   "functools.total_ordering()".

   See the paragraph on "__hash__()" for some important notes on
   creating *hashable* objects which support custom comparison
   operations and are usable as dictionary keys.

   There are no swapped-argument versions of these methods (to be used
   when the left argument does not support the operation but the right
   argument does); rather, "__lt__()" and "__gt__()" are each other's
   reflection, "__le__()" and "__ge__()" are each other's reflection,
   and "__eq__()" and "__ne__()" are their own reflection. If the
   operands are of different types, and right operand's type is a
   direct or indirect subclass of the left operand's type, the
   reflected method of the right operand has priority, otherwise the
   left operand's method has priority.  Virtual subclassing is not
   considered.

object.__hash__(self)

   Called by built-in function "hash()" and for operations on members
   of hashed collections including "set", "frozenset", and "dict".
   "__hash__()" should return an integer. The only required property
   is that objects which compare equal have the same hash value; it is
   advised to mix together the hash values of the components of the
   object that also play a part in comparison of objects by packing
   them into a tuple and hashing the tuple. Example:

      def __hash__(self):
          return hash((self.name, self.nick, self.color))

   Note: "hash()" truncates the value returned from an object's
     custom "__hash__()" method to the size of a "Py_ssize_t".  This
     is typically 8 bytes on 64-bit builds and 4 bytes on 32-bit
     builds. If an object's   "__hash__()" must interoperate on builds
     of different bit sizes, be sure to check the width on all
     supported builds.  An easy way to do this is with "python -c
     "import sys; print(sys.hash_info.width)"".

   If a class does not define an "__eq__()" method it should not
   define a "__hash__()" operation either; if it defines "__eq__()"
   but not "__hash__()", its instances will not be usable as items in
   hashable collections.  If a class defines mutable objects and
   implements an "__eq__()" method, it should not implement
   "__hash__()", since the implementation of hashable collections
   requires that a key's hash value is immutable (if the object's hash
   value changes, it will be in the wrong hash bucket).

   User-defined classes have "__eq__()" and "__hash__()" methods by
   default; with them, all objects compare unequal (except with
   themselves) and "x.__hash__()" returns an appropriate value such
   that "x == y" implies both that "x is y" and "hash(x) == hash(y)".

   A class that overrides "__eq__()" and does not define "__hash__()"
   will have its "__hash__()" implicitly set to "None".  When the
   "__hash__()" method of a class is "None", instances of the class
   will raise an appropriate "TypeError" when a program attempts to
   retrieve their hash value, and will also be correctly identified as
   unhashable when checking "isinstance(obj, collections.Hashable)".

   If a class that overrides "__eq__()" needs to retain the
   implementation of "__hash__()" from a parent class, the interpreter
   must be told this explicitly by setting "__hash__ =
   <ParentClass>.__hash__".

   If a class that does not override "__eq__()" wishes to suppress
   hash support, it should include "__hash__ = None" in the class
   definition. A class which defines its own "__hash__()" that
   explicitly raises a "TypeError" would be incorrectly identified as
   hashable by an "isinstance(obj, collections.Hashable)" call.

   Note: By default, the "__hash__()" values of str, bytes and
     datetime objects are "salted" with an unpredictable random value.
     Although they remain constant within an individual Python
     process, they are not predictable between repeated invocations of
     Python.This is intended to provide protection against a denial-
     of-service caused by carefully-chosen inputs that exploit the
     worst case performance of a dict insertion, O(n^2) complexity.
     See http://www.ocert.org/advisories/ocert-2011-003.html for
     details.Changing hash values affects the iteration order of
     dicts, sets and other mappings.  Python has never made guarantees
     about this ordering (and it typically varies between 32-bit and
     64-bit builds).See also "PYTHONHASHSEED".

   Changed in version 3.3: Hash randomization is enabled by default.

object.__bool__(self)

   Called to implement truth value testing and the built-in operation
   "bool()"; should return "False" or "True".  When this method is not
   defined, "__len__()" is called, if it is defined, and the object is
   considered true if its result is nonzero.  If a class defines
   neither "__len__()" nor "__bool__()", all its instances are
   considered true.
"""
    , 'debugger':
    """"pdb" --- The Python Debugger
*****************************

**Source code:** Lib/pdb.py

======================================================================

The module "pdb" defines an interactive source code debugger for
Python programs.  It supports setting (conditional) breakpoints and
single stepping at the source line level, inspection of stack frames,
source code listing, and evaluation of arbitrary Python code in the
context of any stack frame.  It also supports post-mortem debugging
and can be called under program control.

The debugger is extensible -- it is actually defined as the class
"Pdb". This is currently undocumented but easily understood by reading
the source.  The extension interface uses the modules "bdb" and "cmd".

The debugger's prompt is "(Pdb)". Typical usage to run a program under
control of the debugger is:

   >>> import pdb
   >>> import mymodule
   >>> pdb.run('mymodule.test()')
   > <string>(0)?()
   (Pdb) continue
   > <string>(1)?()
   (Pdb) continue
   NameError: 'spam'
   > <string>(1)?()
   (Pdb)

Changed in version 3.3: Tab-completion via the "readline" module is
available for commands and command arguments, e.g. the current global
and local names are offered as arguments of the "p" command.

"pdb.py" can also be invoked as a script to debug other scripts.  For
example:

   python3 -m pdb myscript.py

When invoked as a script, pdb will automatically enter post-mortem
debugging if the program being debugged exits abnormally.  After post-
mortem debugging (or after normal exit of the program), pdb will
restart the program.  Automatic restarting preserves pdb's state (such
as breakpoints) and in most cases is more useful than quitting the
debugger upon program's exit.

New in version 3.2: "pdb.py" now accepts a "-c" option that executes
commands as if given in a ".pdbrc" file, see Debugger Commands.

The typical usage to break into the debugger from a running program is
to insert

   import pdb; pdb.set_trace()

at the location you want to break into the debugger.  You can then
step through the code following this statement, and continue running
without the debugger using the "continue" command.

The typical usage to inspect a crashed program is:

   >>> import pdb
   >>> import mymodule
   >>> mymodule.test()
   Traceback (most recent call last):
     File "<stdin>", line 1, in <module>
     File "./mymodule.py", line 4, in test
       test2()
     File "./mymodule.py", line 3, in test2
       print(spam)
   NameError: spam
   >>> pdb.pm()
   > ./mymodule.py(3)test2()
   -> print(spam)
   (Pdb)

The module defines the following functions; each enters the debugger
in a slightly different way:

pdb.run(statement, globals=None, locals=None)

   Execute the *statement* (given as a string or a code object) under
   debugger control.  The debugger prompt appears before any code is
   executed; you can set breakpoints and type "continue", or you can
   step through the statement using "step" or "next" (all these
   commands are explained below).  The optional *globals* and *locals*
   arguments specify the environment in which the code is executed; by
   default the dictionary of the module "__main__" is used.  (See the
   explanation of the built-in "exec()" or "eval()" functions.)

pdb.runeval(expression, globals=None, locals=None)

   Evaluate the *expression* (given as a string or a code object)
   under debugger control.  When "runeval()" returns, it returns the
   value of the expression.  Otherwise this function is similar to
   "run()".

pdb.runcall(function, *args, **kwds)

   Call the *function* (a function or method object, not a string)
   with the given arguments.  When "runcall()" returns, it returns
   whatever the function call returned.  The debugger prompt appears
   as soon as the function is entered.

pdb.set_trace()

   Enter the debugger at the calling stack frame.  This is useful to
   hard-code a breakpoint at a given point in a program, even if the
   code is not otherwise being debugged (e.g. when an assertion
   fails).

pdb.post_mortem(traceback=None)

   Enter post-mortem debugging of the given *traceback* object.  If no
   *traceback* is given, it uses the one of the exception that is
   currently being handled (an exception must be being handled if the
   default is to be used).

pdb.pm()

   Enter post-mortem debugging of the traceback found in
   "sys.last_traceback".

The "run*" functions and "set_trace()" are aliases for instantiating
the "Pdb" class and calling the method of the same name.  If you want
to access further features, you have to do this yourself:

class pdb.Pdb(completekey='tab', stdin=None, stdout=None, skip=None, nosigint=False, readrc=True)

   "Pdb" is the debugger class.

   The *completekey*, *stdin* and *stdout* arguments are passed to the
   underlying "cmd.Cmd" class; see the description there.

   The *skip* argument, if given, must be an iterable of glob-style
   module name patterns.  The debugger will not step into frames that
   originate in a module that matches one of these patterns. [1]

   By default, Pdb sets a handler for the SIGINT signal (which is sent
   when the user presses "Ctrl-C" on the console) when you give a
   "continue" command. This allows you to break into the debugger
   again by pressing "Ctrl-C".  If you want Pdb not to touch the
   SIGINT handler, set *nosigint* to true.

   The *readrc* argument defaults to true and controls whether Pdb
   will load .pdbrc files from the filesystem.

   Example call to enable tracing with *skip*:

      import pdb; pdb.Pdb(skip=['django.*']).set_trace()

   New in version 3.1: The *skip* argument.

   New in version 3.2: The *nosigint* argument.  Previously, a SIGINT
   handler was never set by Pdb.

   Changed in version 3.6: The *readrc* argument.

   run(statement, globals=None, locals=None)
   runeval(expression, globals=None, locals=None)
   runcall(function, *args, **kwds)
   set_trace()

      See the documentation for the functions explained above.


Debugger Commands
=================

The commands recognized by the debugger are listed below.  Most
commands can be abbreviated to one or two letters as indicated; e.g.
"h(elp)" means that either "h" or "help" can be used to enter the help
command (but not "he" or "hel", nor "H" or "Help" or "HELP").
Arguments to commands must be separated by whitespace (spaces or
tabs).  Optional arguments are enclosed in square brackets ("[]") in
the command syntax; the square brackets must not be typed.
Alternatives in the command syntax are separated by a vertical bar
("|").

Entering a blank line repeats the last command entered.  Exception: if
the last command was a "list" command, the next 11 lines are listed.

Commands that the debugger doesn't recognize are assumed to be Python
statements and are executed in the context of the program being
debugged.  Python statements can also be prefixed with an exclamation
point ("!").  This is a powerful way to inspect the program being
debugged; it is even possible to change a variable or call a function.
When an exception occurs in such a statement, the exception name is
printed but the debugger's state is not changed.

The debugger supports aliases.  Aliases can have parameters which
allows one a certain level of adaptability to the context under
examination.

Multiple commands may be entered on a single line, separated by ";;".
(A single ";" is not used as it is the separator for multiple commands
in a line that is passed to the Python parser.)  No intelligence is
applied to separating the commands; the input is split at the first
";;" pair, even if it is in the middle of a quoted string.

If a file ".pdbrc" exists in the user's home directory or in the
current directory, it is read in and executed as if it had been typed
at the debugger prompt.  This is particularly useful for aliases.  If
both files exist, the one in the home directory is read first and
aliases defined there can be overridden by the local file.

Changed in version 3.2: ".pdbrc" can now contain commands that
continue debugging, such as "continue" or "next".  Previously, these
commands had no effect.

h(elp) [command]

   Without argument, print the list of available commands.  With a
   *command* as argument, print help about that command.  "help pdb"
   displays the full documentation (the docstring of the "pdb"
   module).  Since the *command* argument must be an identifier, "help
   exec" must be entered to get help on the "!" command.

w(here)

   Print a stack trace, with the most recent frame at the bottom.  An
   arrow indicates the current frame, which determines the context of
   most commands.

d(own) [count]

   Move the current frame *count* (default one) levels down in the
   stack trace (to a newer frame).

u(p) [count]

   Move the current frame *count* (default one) levels up in the stack
   trace (to an older frame).

b(reak) [([filename:]lineno | function) [, condition]]

   With a *lineno* argument, set a break there in the current file.
   With a *function* argument, set a break at the first executable
   statement within that function.  The line number may be prefixed
   with a filename and a colon, to specify a breakpoint in another
   file (probably one that hasn't been loaded yet).  The file is
   searched on "sys.path".  Note that each breakpoint is assigned a
   number to which all the other breakpoint commands refer.

   If a second argument is present, it is an expression which must
   evaluate to true before the breakpoint is honored.

   Without argument, list all breaks, including for each breakpoint,
   the number of times that breakpoint has been hit, the current
   ignore count, and the associated condition if any.

tbreak [([filename:]lineno | function) [, condition]]

   Temporary breakpoint, which is removed automatically when it is
   first hit. The arguments are the same as for "break".

cl(ear) [filename:lineno | bpnumber [bpnumber ...]]

   With a *filename:lineno* argument, clear all the breakpoints at
   this line. With a space separated list of breakpoint numbers, clear
   those breakpoints. Without argument, clear all breaks (but first
   ask confirmation).

disable [bpnumber [bpnumber ...]]

   Disable the breakpoints given as a space separated list of
   breakpoint numbers.  Disabling a breakpoint means it cannot cause
   the program to stop execution, but unlike clearing a breakpoint, it
   remains in the list of breakpoints and can be (re-)enabled.

enable [bpnumber [bpnumber ...]]

   Enable the breakpoints specified.

ignore bpnumber [count]

   Set the ignore count for the given breakpoint number.  If count is
   omitted, the ignore count is set to 0.  A breakpoint becomes active
   when the ignore count is zero.  When non-zero, the count is
   decremented each time the breakpoint is reached and the breakpoint
   is not disabled and any associated condition evaluates to true.

condition bpnumber [condition]

   Set a new *condition* for the breakpoint, an expression which must
   evaluate to true before the breakpoint is honored.  If *condition*
   is absent, any existing condition is removed; i.e., the breakpoint
   is made unconditional.

commands [bpnumber]

   Specify a list of commands for breakpoint number *bpnumber*.  The
   commands themselves appear on the following lines.  Type a line
   containing just "end" to terminate the commands. An example:

      (Pdb) commands 1
      (com) p some_variable
      (com) end
      (Pdb)

   To remove all commands from a breakpoint, type commands and follow
   it immediately with "end"; that is, give no commands.

   With no *bpnumber* argument, commands refers to the last breakpoint
   set.

   You can use breakpoint commands to start your program up again.
   Simply use the continue command, or step, or any other command that
   resumes execution.

   Specifying any command resuming execution (currently continue,
   step, next, return, jump, quit and their abbreviations) terminates
   the command list (as if that command was immediately followed by
   end). This is because any time you resume execution (even with a
   simple next or step), you may encounter another breakpoint—which
   could have its own command list, leading to ambiguities about which
   list to execute.

   If you use the 'silent' command in the command list, the usual
   message about stopping at a breakpoint is not printed.  This may be
   desirable for breakpoints that are to print a specific message and
   then continue.  If none of the other commands print anything, you
   see no sign that the breakpoint was reached.

s(tep)

   Execute the current line, stop at the first possible occasion
   (either in a function that is called or on the next line in the
   current function).

n(ext)

   Continue execution until the next line in the current function is
   reached or it returns.  (The difference between "next" and "step"
   is that "step" stops inside a called function, while "next"
   executes called functions at (nearly) full speed, only stopping at
   the next line in the current function.)

unt(il) [lineno]

   Without argument, continue execution until the line with a number
   greater than the current one is reached.

   With a line number, continue execution until a line with a number
   greater or equal to that is reached.  In both cases, also stop when
   the current frame returns.

   Changed in version 3.2: Allow giving an explicit line number.

r(eturn)

   Continue execution until the current function returns.

c(ont(inue))

   Continue execution, only stop when a breakpoint is encountered.

j(ump) lineno

   Set the next line that will be executed.  Only available in the
   bottom-most frame.  This lets you jump back and execute code again,
   or jump forward to skip code that you don't want to run.

   It should be noted that not all jumps are allowed -- for instance
   it is not possible to jump into the middle of a "for" loop or out
   of a "finally" clause.

l(ist) [first[, last]]

   List source code for the current file.  Without arguments, list 11
   lines around the current line or continue the previous listing.
   With "." as argument, list 11 lines around the current line.  With
   one argument, list 11 lines around at that line.  With two
   arguments, list the given range; if the second argument is less
   than the first, it is interpreted as a count.

   The current line in the current frame is indicated by "->".  If an
   exception is being debugged, the line where the exception was
   originally raised or propagated is indicated by ">>", if it differs
   from the current line.

   New in version 3.2: The ">>" marker.

ll | longlist

   List all source code for the current function or frame.
   Interesting lines are marked as for "list".

   New in version 3.2.

a(rgs)

   Print the argument list of the current function.

p expression

   Evaluate the *expression* in the current context and print its
   value.

   Note: "print()" can also be used, but is not a debugger command
     --- this executes the Python "print()" function.

pp expression

   Like the "p" command, except the value of the expression is pretty-
   printed using the "pprint" module.

whatis expression

   Print the type of the *expression*.

source expression

   Try to get source code for the given object and display it.

   New in version 3.2.

display [expression]

   Display the value of the expression if it changed, each time
   execution stops in the current frame.

   Without expression, list all display expressions for the current
   frame.

   New in version 3.2.

undisplay [expression]

   Do not display the expression any more in the current frame.
   Without expression, clear all display expressions for the current
   frame.

   New in version 3.2.

interact

   Start an interactive interpreter (using the "code" module) whose
   global namespace contains all the (global and local) names found in
   the current scope.

   New in version 3.2.

alias [name [command]]

   Create an alias called *name* that executes *command*.  The command
   must *not* be enclosed in quotes.  Replaceable parameters can be
   indicated by "%1", "%2", and so on, while "%*" is replaced by all
   the parameters. If no command is given, the current alias for
   *name* is shown. If no arguments are given, all aliases are listed.

   Aliases may be nested and can contain anything that can be legally
   typed at the pdb prompt.  Note that internal pdb commands *can* be
   overridden by aliases.  Such a command is then hidden until the
   alias is removed.  Aliasing is recursively applied to the first
   word of the command line; all other words in the line are left
   alone.

   As an example, here are two useful aliases (especially when placed
   in the ".pdbrc" file):

      # Print instance variables (usage "pi classInst")
      alias pi for k in %1.__dict__.keys(): print("%1.",k,"=",%1.__dict__[k])
      # Print instance variables in self
      alias ps pi self

unalias name

   Delete the specified alias.

! statement

   Execute the (one-line) *statement* in the context of the current
   stack frame. The exclamation point can be omitted unless the first
   word of the statement resembles a debugger command.  To set a
   global variable, you can prefix the assignment command with a
   "global" statement on the same line, e.g.:

      (Pdb) global list_options; list_options = ['-l']
      (Pdb)

run [args ...]
restart [args ...]

   Restart the debugged Python program.  If an argument is supplied,
   it is split with "shlex" and the result is used as the new
   "sys.argv". History, breakpoints, actions and debugger options are
   preserved. "restart" is an alias for "run".

q(uit)

   Quit from the debugger.  The program being executed is aborted.

-[ Footnotes ]-

[1] Whether a frame is considered to originate in a certain module
    is determined by the "__name__" in the frame globals.
"""
    , 'del':
    """The "del" statement
*******************

   del_stmt ::= "del" target_list

Deletion is recursively defined very similar to the way assignment is
defined. Rather than spelling it out in full details, here are some
hints.

Deletion of a target list recursively deletes each target, from left
to right.

Deletion of a name removes the binding of that name from the local or
global namespace, depending on whether the name occurs in a "global"
statement in the same code block.  If the name is unbound, a
"NameError" exception will be raised.

Deletion of attribute references, subscriptions and slicings is passed
to the primary object involved; deletion of a slicing is in general
equivalent to assignment of an empty slice of the right type (but even
this is determined by the sliced object).

Changed in version 3.2: Previously it was illegal to delete a name
from the local namespace if it occurs as a free variable in a nested
block.
"""
    , 'dict':
    """Dictionary displays
*******************

A dictionary display is a possibly empty series of key/datum pairs
enclosed in curly braces:

   dict_display       ::= "{" [key_datum_list | dict_comprehension] "}"
   key_datum_list     ::= key_datum ("," key_datum)* [","]
   key_datum          ::= expression ":" expression | "**" or_expr
   dict_comprehension ::= expression ":" expression comp_for

A dictionary display yields a new dictionary object.

If a comma-separated sequence of key/datum pairs is given, they are
evaluated from left to right to define the entries of the dictionary:
each key object is used as a key into the dictionary to store the
corresponding datum.  This means that you can specify the same key
multiple times in the key/datum list, and the final dictionary's value
for that key will be the last one given.

A double asterisk "**" denotes *dictionary unpacking*. Its operand
must be a *mapping*.  Each mapping item is added to the new
dictionary.  Later values replace values already set by earlier
key/datum pairs and earlier dictionary unpackings.

New in version 3.5: Unpacking into dictionary displays, originally
proposed by **PEP 448**.

A dict comprehension, in contrast to list and set comprehensions,
needs two expressions separated with a colon followed by the usual
"for" and "if" clauses. When the comprehension is run, the resulting
key and value elements are inserted in the new dictionary in the order
they are produced.

Restrictions on the types of the key values are listed earlier in
section The standard type hierarchy.  (To summarize, the key type
should be *hashable*, which excludes all mutable objects.)  Clashes
between duplicate keys are not detected; the last datum (textually
rightmost in the display) stored for a given key value prevails.
"""
    , 'dynamic-features':
    """Interaction with dynamic features
*********************************

Name resolution of free variables occurs at runtime, not at compile
time. This means that the following code will print 42:

   i = 10
   def f():
       print(i)
   i = 42
   f()

The "eval()" and "exec()" functions do not have access to the full
environment for resolving names.  Names may be resolved in the local
and global namespaces of the caller.  Free variables are not resolved
in the nearest enclosing namespace, but in the global namespace.  [1]
The "exec()" and "eval()" functions have optional arguments to
override the global and local namespace.  If only one namespace is
specified, it is used for both.
"""
    , 'else':
    """The "if" statement
******************

The "if" statement is used for conditional execution:

   if_stmt ::= "if" expression ":" suite
               ( "elif" expression ":" suite )*
               ["else" ":" suite]

It selects exactly one of the suites by evaluating the expressions one
by one until one is found to be true (see section Boolean operations
for the definition of true and false); then that suite is executed
(and no other part of the "if" statement is executed or evaluated).
If all expressions are false, the suite of the "else" clause, if
present, is executed.
"""
    , 'exceptions':
    """Exceptions
**********

Exceptions are a means of breaking out of the normal flow of control
of a code block in order to handle errors or other exceptional
conditions.  An exception is *raised* at the point where the error is
detected; it may be *handled* by the surrounding code block or by any
code block that directly or indirectly invoked the code block where
the error occurred.

The Python interpreter raises an exception when it detects a run-time
error (such as division by zero).  A Python program can also
explicitly raise an exception with the "raise" statement. Exception
handlers are specified with the "try" ... "except" statement.  The
"finally" clause of such a statement can be used to specify cleanup
code which does not handle the exception, but is executed whether an
exception occurred or not in the preceding code.

Python uses the "termination" model of error handling: an exception
handler can find out what happened and continue execution at an outer
level, but it cannot repair the cause of the error and retry the
failing operation (except by re-entering the offending piece of code
from the top).

When an exception is not handled at all, the interpreter terminates
execution of the program, or returns to its interactive main loop.  In
either case, it prints a stack backtrace, except when the exception is
"SystemExit".

Exceptions are identified by class instances.  The "except" clause is
selected depending on the class of the instance: it must reference the
class of the instance or a base class thereof.  The instance can be
received by the handler and can carry additional information about the
exceptional condition.

Note: Exception messages are not part of the Python API.  Their
  contents may change from one version of Python to the next without
  warning and should not be relied on by code which will run under
  multiple versions of the interpreter.

See also the description of the "try" statement in section The try
statement and "raise" statement in section The raise statement.

-[ Footnotes ]-

[1] This limitation occurs because the code that is executed by
    these operations is not available at the time the module is
    compiled.
"""
    , 'execmodel':
    """Execution model
***************


Structure of a program
======================

A Python program is constructed from code blocks. A *block* is a piece
of Python program text that is executed as a unit. The following are
blocks: a module, a function body, and a class definition. Each
command typed interactively is a block.  A script file (a file given
as standard input to the interpreter or specified as a command line
argument to the interpreter) is a code block.  A script command (a
command specified on the interpreter command line with the '**-c**'
option) is a code block.  The string argument passed to the built-in
functions "eval()" and "exec()" is a code block.

A code block is executed in an *execution frame*.  A frame contains
some administrative information (used for debugging) and determines
where and how execution continues after the code block's execution has
completed.


Naming and binding
==================


Binding of names
----------------

*Names* refer to objects.  Names are introduced by name binding
operations.

The following constructs bind names: formal parameters to functions,
"import" statements, class and function definitions (these bind the
class or function name in the defining block), and targets that are
identifiers if occurring in an assignment, "for" loop header, or after
"as" in a "with" statement or "except" clause. The "import" statement
of the form "from ... import *" binds all names defined in the
imported module, except those beginning with an underscore.  This form
may only be used at the module level.

A target occurring in a "del" statement is also considered bound for
this purpose (though the actual semantics are to unbind the name).

Each assignment or import statement occurs within a block defined by a
class or function definition or at the module level (the top-level
code block).

If a name is bound in a block, it is a local variable of that block,
unless declared as "nonlocal" or "global".  If a name is bound at the
module level, it is a global variable.  (The variables of the module
code block are local and global.)  If a variable is used in a code
block but not defined there, it is a *free variable*.

Each occurrence of a name in the program text refers to the *binding*
of that name established by the following name resolution rules.


Resolution of names
-------------------

A *scope* defines the visibility of a name within a block.  If a local
variable is defined in a block, its scope includes that block.  If the
definition occurs in a function block, the scope extends to any blocks
contained within the defining one, unless a contained block introduces
a different binding for the name.

When a name is used in a code block, it is resolved using the nearest
enclosing scope.  The set of all such scopes visible to a code block
is called the block's *environment*.

When a name is not found at all, a "NameError" exception is raised. If
the current scope is a function scope, and the name refers to a local
variable that has not yet been bound to a value at the point where the
name is used, an "UnboundLocalError" exception is raised.
"UnboundLocalError" is a subclass of "NameError".

If a name binding operation occurs anywhere within a code block, all
uses of the name within the block are treated as references to the
current block.  This can lead to errors when a name is used within a
block before it is bound.  This rule is subtle.  Python lacks
declarations and allows name binding operations to occur anywhere
within a code block.  The local variables of a code block can be
determined by scanning the entire text of the block for name binding
operations.

If the "global" statement occurs within a block, all uses of the name
specified in the statement refer to the binding of that name in the
top-level namespace.  Names are resolved in the top-level namespace by
searching the global namespace, i.e. the namespace of the module
containing the code block, and the builtins namespace, the namespace
of the module "builtins".  The global namespace is searched first.  If
the name is not found there, the builtins namespace is searched.  The
"global" statement must precede all uses of the name.

The "global" statement has the same scope as a name binding operation
in the same block.  If the nearest enclosing scope for a free variable
contains a global statement, the free variable is treated as a global.

The "nonlocal" statement causes corresponding names to refer to
previously bound variables in the nearest enclosing function scope.
"SyntaxError" is raised at compile time if the given name does not
exist in any enclosing function scope.

The namespace for a module is automatically created the first time a
module is imported.  The main module for a script is always called
"__main__".

Class definition blocks and arguments to "exec()" and "eval()" are
special in the context of name resolution. A class definition is an
executable statement that may use and define names. These references
follow the normal rules for name resolution with an exception that
unbound local variables are looked up in the global namespace. The
namespace of the class definition becomes the attribute dictionary of
the class. The scope of names defined in a class block is limited to
the class block; it does not extend to the code blocks of methods --
this includes comprehensions and generator expressions since they are
implemented using a function scope.  This means that the following
will fail:

   class A:
       a = 42
       b = list(a + i for i in range(10))


Builtins and restricted execution
---------------------------------

**CPython implementation detail:** Users should not touch
"__builtins__"; it is strictly an implementation detail.  Users
wanting to override values in the builtins namespace should "import"
the "builtins" module and modify its attributes appropriately.

The builtins namespace associated with the execution of a code block
is actually found by looking up the name "__builtins__" in its global
namespace; this should be a dictionary or a module (in the latter case
the module's dictionary is used).  By default, when in the "__main__"
module, "__builtins__" is the built-in module "builtins"; when in any
other module, "__builtins__" is an alias for the dictionary of the
"builtins" module itself.


Interaction with dynamic features
---------------------------------

Name resolution of free variables occurs at runtime, not at compile
time. This means that the following code will print 42:

   i = 10
   def f():
       print(i)
   i = 42
   f()

The "eval()" and "exec()" functions do not have access to the full
environment for resolving names.  Names may be resolved in the local
and global namespaces of the caller.  Free variables are not resolved
in the nearest enclosing namespace, but in the global namespace.  [1]
The "exec()" and "eval()" functions have optional arguments to
override the global and local namespace.  If only one namespace is
specified, it is used for both.


Exceptions
==========

Exceptions are a means of breaking out of the normal flow of control
of a code block in order to handle errors or other exceptional
conditions.  An exception is *raised* at the point where the error is
detected; it may be *handled* by the surrounding code block or by any
code block that directly or indirectly invoked the code block where
the error occurred.

The Python interpreter raises an exception when it detects a run-time
error (such as division by zero).  A Python program can also
explicitly raise an exception with the "raise" statement. Exception
handlers are specified with the "try" ... "except" statement.  The
"finally" clause of such a statement can be used to specify cleanup
code which does not handle the exception, but is executed whether an
exception occurred or not in the preceding code.

Python uses the "termination" model of error handling: an exception
handler can find out what happened and continue execution at an outer
level, but it cannot repair the cause of the error and retry the
failing operation (except by re-entering the offending piece of code
from the top).

When an exception is not handled at all, the interpreter terminates
execution of the program, or returns to its interactive main loop.  In
either case, it prints a stack backtrace, except when the exception is
"SystemExit".

Exceptions are identified by class instances.  The "except" clause is
selected depending on the class of the instance: it must reference the
class of the instance or a base class thereof.  The instance can be
received by the handler and can carry additional information about the
exceptional condition.

Note: Exception messages are not part of the Python API.  Their
  contents may change from one version of Python to the next without
  warning and should not be relied on by code which will run under
  multiple versions of the interpreter.

See also the description of the "try" statement in section The try
statement and "raise" statement in section The raise statement.

-[ Footnotes ]-

[1] This limitation occurs because the code that is executed by
    these operations is not available at the time the module is
    compiled.
"""
    , 'exprlists':
    """Expression lists
****************

   expression_list    ::= expression ( "," expression )* [","]
   starred_list       ::= starred_item ( "," starred_item )* [","]
   starred_expression ::= expression | ( starred_item "," )* [starred_item]
   starred_item       ::= expression | "*" or_expr

Except when part of a list or set display, an expression list
containing at least one comma yields a tuple.  The length of the tuple
is the number of expressions in the list.  The expressions are
evaluated from left to right.

An asterisk "*" denotes *iterable unpacking*.  Its operand must be an
*iterable*.  The iterable is expanded into a sequence of items, which
are included in the new tuple, list, or set, at the site of the
unpacking.

New in version 3.5: Iterable unpacking in expression lists, originally
proposed by **PEP 448**.

The trailing comma is required only to create a single tuple (a.k.a. a
*singleton*); it is optional in all other cases.  A single expression
without a trailing comma doesn't create a tuple, but rather yields the
value of that expression. (To create an empty tuple, use an empty pair
of parentheses: "()".)
"""
    , 'floating':
    """Floating point literals
***********************

Floating point literals are described by the following lexical
definitions:

   floatnumber   ::= pointfloat | exponentfloat
   pointfloat    ::= [digitpart] fraction | digitpart "."
   exponentfloat ::= (digitpart | pointfloat) exponent
   digitpart     ::= digit (["_"] digit)*
   fraction      ::= "." digitpart
   exponent      ::= ("e" | "E") ["+" | "-"] digitpart

Note that the integer and exponent parts are always interpreted using
radix 10. For example, "077e010" is legal, and denotes the same number
as "77e10". The allowed range of floating point literals is
implementation-dependent.  As in integer literals, underscores are
supported for digit grouping.

Some examples of floating point literals:

   3.14    10.    .001    1e100    3.14e-10    0e0    3.14_15_93

Note that numeric literals do not include a sign; a phrase like "-1"
is actually an expression composed of the unary operator "-" and the
literal "1".

Changed in version 3.6: Underscores are now allowed for grouping
purposes in literals.
"""
    , 'for':
    """The "for" statement
*******************

The "for" statement is used to iterate over the elements of a sequence
(such as a string, tuple or list) or other iterable object:

   for_stmt ::= "for" target_list "in" expression_list ":" suite
                ["else" ":" suite]

The expression list is evaluated once; it should yield an iterable
object.  An iterator is created for the result of the
"expression_list".  The suite is then executed once for each item
provided by the iterator, in the order returned by the iterator.  Each
item in turn is assigned to the target list using the standard rules
for assignments (see Assignment statements), and then the suite is
executed.  When the items are exhausted (which is immediately when the
sequence is empty or an iterator raises a "StopIteration" exception),
the suite in the "else" clause, if present, is executed, and the loop
terminates.

A "break" statement executed in the first suite terminates the loop
without executing the "else" clause's suite.  A "continue" statement
executed in the first suite skips the rest of the suite and continues
with the next item, or with the "else" clause if there is no next
item.

The for-loop makes assignments to the variables(s) in the target list.
This overwrites all previous assignments to those variables including
those made in the suite of the for-loop:

   for i in range(10):
       print(i)
       i = 5             # this will not affect the for-loop
                         # because i will be overwritten with the next
                         # index in the range

Names in the target list are not deleted when the loop is finished,
but if the sequence is empty, they will not have been assigned to at
all by the loop.  Hint: the built-in function "range()" returns an
iterator of integers suitable to emulate the effect of Pascal's "for i
:= a to b do"; e.g., "list(range(3))" returns the list "[0, 1, 2]".

Note: There is a subtlety when the sequence is being modified by the
  loop (this can only occur for mutable sequences, i.e. lists).  An
  internal counter is used to keep track of which item is used next,
  and this is incremented on each iteration.  When this counter has
  reached the length of the sequence the loop terminates.  This means
  that if the suite deletes the current (or a previous) item from the
  sequence, the next item will be skipped (since it gets the index of
  the current item which has already been treated).  Likewise, if the
  suite inserts an item in the sequence before the current item, the
  current item will be treated again the next time through the loop.
  This can lead to nasty bugs that can be avoided by making a
  temporary copy using a slice of the whole sequence, e.g.,

     for x in a[:]:
         if x < 0: a.remove(x)
"""
    , 'formatstrings':
    """Format String Syntax
********************

The "str.format()" method and the "Formatter" class share the same
syntax for format strings (although in the case of "Formatter",
subclasses can define their own format string syntax).  The syntax is
related to that of formatted string literals, but there are
differences.

Format strings contain "replacement fields" surrounded by curly braces
"{}". Anything that is not contained in braces is considered literal
text, which is copied unchanged to the output.  If you need to include
a brace character in the literal text, it can be escaped by doubling:
"{{" and "}}".

The grammar for a replacement field is as follows:

      replacement_field ::= "{" [field_name] ["!" conversion] [":" format_spec] "}"
      field_name        ::= arg_name ("." attribute_name | "[" element_index "]")*
      arg_name          ::= [identifier | integer]
      attribute_name    ::= identifier
      element_index     ::= integer | index_string
      index_string      ::= <any source character except "]"> +
      conversion        ::= "r" | "s" | "a"
      format_spec       ::= <described in the next section>

In less formal terms, the replacement field can start with a
*field_name* that specifies the object whose value is to be formatted
and inserted into the output instead of the replacement field. The
*field_name* is optionally followed by a  *conversion* field, which is
preceded by an exclamation point "'!'", and a *format_spec*, which is
preceded by a colon "':'".  These specify a non-default format for the
replacement value.

See also the Format Specification Mini-Language section.

The *field_name* itself begins with an *arg_name* that is either a
number or a keyword.  If it's a number, it refers to a positional
argument, and if it's a keyword, it refers to a named keyword
argument.  If the numerical arg_names in a format string are 0, 1, 2,
... in sequence, they can all be omitted (not just some) and the
numbers 0, 1, 2, ... will be automatically inserted in that order.
Because *arg_name* is not quote-delimited, it is not possible to
specify arbitrary dictionary keys (e.g., the strings "'10'" or
"':-]'") within a format string. The *arg_name* can be followed by any
number of index or attribute expressions. An expression of the form
"'.name'" selects the named attribute using "getattr()", while an
expression of the form "'[index]'" does an index lookup using
"__getitem__()".

Changed in version 3.1: The positional argument specifiers can be
omitted, so "'{} {}'" is equivalent to "'{0} {1}'".

Some simple format string examples:

   "First, thou shalt count to {0}"  # References first positional argument
   "Bring me a {}"                   # Implicitly references the first positional argument
   "From {} to {}"                   # Same as "From {0} to {1}"
   "My quest is {name}"              # References keyword argument 'name'
   "Weight in tons {0.weight}"       # 'weight' attribute of first positional arg
   "Units destroyed: {players[0]}"   # First element of keyword argument 'players'.

The *conversion* field causes a type coercion before formatting.
Normally, the job of formatting a value is done by the "__format__()"
method of the value itself.  However, in some cases it is desirable to
force a type to be formatted as a string, overriding its own
definition of formatting.  By converting the value to a string before
calling "__format__()", the normal formatting logic is bypassed.

Three conversion flags are currently supported: "'!s'" which calls
"str()" on the value, "'!r'" which calls "repr()" and "'!a'" which
calls "ascii()".

Some examples:

   "Harold's a clever {0!s}"        # Calls str() on the argument first
   "Bring out the holy {name!r}"    # Calls repr() on the argument first
   "More {!a}"                      # Calls ascii() on the argument first

The *format_spec* field contains a specification of how the value
should be presented, including such details as field width, alignment,
padding, decimal precision and so on.  Each value type can define its
own "formatting mini-language" or interpretation of the *format_spec*.

Most built-in types support a common formatting mini-language, which
is described in the next section.

A *format_spec* field can also include nested replacement fields
within it. These nested replacement fields may contain a field name,
conversion flag and format specification, but deeper nesting is not
allowed.  The replacement fields within the format_spec are
substituted before the *format_spec* string is interpreted. This
allows the formatting of a value to be dynamically specified.

See the Format examples section for some examples.


Format Specification Mini-Language
==================================

"Format specifications" are used within replacement fields contained
within a format string to define how individual values are presented
(see Format String Syntax and Formatted string literals). They can
also be passed directly to the built-in "format()" function.  Each
formattable type may define how the format specification is to be
interpreted.

Most built-in types implement the following options for format
specifications, although some of the formatting options are only
supported by the numeric types.

A general convention is that an empty format string (""\"") produces
the same result as if you had called "str()" on the value. A non-empty
format string typically modifies the result.

The general form of a *standard format specifier* is:

   format_spec     ::= [[fill]align][sign][#][0][width][grouping_option][.precision][type]
   fill            ::= <any character>
   align           ::= "<" | ">" | "=" | "^"
   sign            ::= "+" | "-" | " "
   width           ::= integer
   grouping_option ::= "_" | ","
   precision       ::= integer
   type            ::= "b" | "c" | "d" | "e" | "E" | "f" | "F" | "g" | "G" | "n" | "o" | "s" | "x" | "X" | "%"

If a valid *align* value is specified, it can be preceded by a *fill*
character that can be any character and defaults to a space if
omitted. It is not possible to use a literal curly brace (""{"" or
""}"") as the *fill* character in a formatted string literal or when
using the "str.format()" method.  However, it is possible to insert a
curly brace with a nested replacement field.  This limitation doesn't
affect the "format()" function.

The meaning of the various alignment options is as follows:

   +-----------+------------------------------------------------------------+
   | Option    | Meaning                                                    |
   +===========+============================================================+
   | "'<'"     | Forces the field to be left-aligned within the available   |
   |           | space (this is the default for most objects).              |
   +-----------+------------------------------------------------------------+
   | "'>'"     | Forces the field to be right-aligned within the available  |
   |           | space (this is the default for numbers).                   |
   +-----------+------------------------------------------------------------+
   | "'='"     | Forces the padding to be placed after the sign (if any)    |
   |           | but before the digits.  This is used for printing fields   |
   |           | in the form '+000000120'. This alignment option is only    |
   |           | valid for numeric types.  It becomes the default when '0'  |
   |           | immediately precedes the field width.                      |
   +-----------+------------------------------------------------------------+
   | "'^'"     | Forces the field to be centered within the available       |
   |           | space.                                                     |
   +-----------+------------------------------------------------------------+

Note that unless a minimum field width is defined, the field width
will always be the same size as the data to fill it, so that the
alignment option has no meaning in this case.

The *sign* option is only valid for number types, and can be one of
the following:

   +-----------+------------------------------------------------------------+
   | Option    | Meaning                                                    |
   +===========+============================================================+
   | "'+'"     | indicates that a sign should be used for both positive as  |
   |           | well as negative numbers.                                  |
   +-----------+------------------------------------------------------------+
   | "'-'"     | indicates that a sign should be used only for negative     |
   |           | numbers (this is the default behavior).                    |
   +-----------+------------------------------------------------------------+
   | space     | indicates that a leading space should be used on positive  |
   |           | numbers, and a minus sign on negative numbers.             |
   +-----------+------------------------------------------------------------+

The "'#'" option causes the "alternate form" to be used for the
conversion.  The alternate form is defined differently for different
types.  This option is only valid for integer, float, complex and
Decimal types. For integers, when binary, octal, or hexadecimal output
is used, this option adds the prefix respective "'0b'", "'0o'", or
"'0x'" to the output value. For floats, complex and Decimal the
alternate form causes the result of the conversion to always contain a
decimal-point character, even if no digits follow it. Normally, a
decimal-point character appears in the result of these conversions
only if a digit follows it. In addition, for "'g'" and "'G'"
conversions, trailing zeros are not removed from the result.

The "','" option signals the use of a comma for a thousands separator.
For a locale aware separator, use the "'n'" integer presentation type
instead.

Changed in version 3.1: Added the "','" option (see also **PEP 378**).

The "'_'" option signals the use of an underscore for a thousands
separator for floating point presentation types and for integer
presentation type "'d'".  For integer presentation types "'b'", "'o'",
"'x'", and "'X'", underscores will be inserted every 4 digits.  For
other presentation types, specifying this option is an error.

Changed in version 3.6: Added the "'_'" option (see also **PEP 515**).

*width* is a decimal integer defining the minimum field width.  If not
specified, then the field width will be determined by the content.

When no explicit alignment is given, preceding the *width* field by a
zero ("'0'") character enables sign-aware zero-padding for numeric
types.  This is equivalent to a *fill* character of "'0'" with an
*alignment* type of "'='".

The *precision* is a decimal number indicating how many digits should
be displayed after the decimal point for a floating point value
formatted with "'f'" and "'F'", or before and after the decimal point
for a floating point value formatted with "'g'" or "'G'".  For non-
number types the field indicates the maximum field size - in other
words, how many characters will be used from the field content. The
*precision* is not allowed for integer values.

Finally, the *type* determines how the data should be presented.

The available string presentation types are:

   +-----------+------------------------------------------------------------+
   | Type      | Meaning                                                    |
   +===========+============================================================+
   | "'s'"     | String format. This is the default type for strings and    |
   |           | may be omitted.                                            |
   +-----------+------------------------------------------------------------+
   | None      | The same as "'s'".                                         |
   +-----------+------------------------------------------------------------+

The available integer presentation types are:

   +-----------+------------------------------------------------------------+
   | Type      | Meaning                                                    |
   +===========+============================================================+
   | "'b'"     | Binary format. Outputs the number in base 2.               |
   +-----------+------------------------------------------------------------+
   | "'c'"     | Character. Converts the integer to the corresponding       |
   |           | unicode character before printing.                         |
   +-----------+------------------------------------------------------------+
   | "'d'"     | Decimal Integer. Outputs the number in base 10.            |
   +-----------+------------------------------------------------------------+
   | "'o'"     | Octal format. Outputs the number in base 8.                |
   +-----------+------------------------------------------------------------+
   | "'x'"     | Hex format. Outputs the number in base 16, using lower-    |
   |           | case letters for the digits above 9.                       |
   +-----------+------------------------------------------------------------+
   | "'X'"     | Hex format. Outputs the number in base 16, using upper-    |
   |           | case letters for the digits above 9.                       |
   +-----------+------------------------------------------------------------+
   | "'n'"     | Number. This is the same as "'d'", except that it uses the |
   |           | current locale setting to insert the appropriate number    |
   |           | separator characters.                                      |
   +-----------+------------------------------------------------------------+
   | None      | The same as "'d'".                                         |
   +-----------+------------------------------------------------------------+

In addition to the above presentation types, integers can be formatted
with the floating point presentation types listed below (except "'n'"
and "None"). When doing so, "float()" is used to convert the integer
to a floating point number before formatting.

The available presentation types for floating point and decimal values
are:

   +-----------+------------------------------------------------------------+
   | Type      | Meaning                                                    |
   +===========+============================================================+
   | "'e'"     | Exponent notation. Prints the number in scientific         |
   |           | notation using the letter 'e' to indicate the exponent.    |
   |           | The default precision is "6".                              |
   +-----------+------------------------------------------------------------+
   | "'E'"     | Exponent notation. Same as "'e'" except it uses an upper   |
   |           | case 'E' as the separator character.                       |
   +-----------+------------------------------------------------------------+
   | "'f'"     | Fixed point. Displays the number as a fixed-point number.  |
   |           | The default precision is "6".                              |
   +-----------+------------------------------------------------------------+
   | "'F'"     | Fixed point. Same as "'f'", but converts "nan" to "NAN"    |
   |           | and "inf" to "INF".                                        |
   +-----------+------------------------------------------------------------+
   | "'g'"     | General format.  For a given precision "p >= 1", this      |
   |           | rounds the number to "p" significant digits and then       |
   |           | formats the result in either fixed-point format or in      |
   |           | scientific notation, depending on its magnitude.  The      |
   |           | precise rules are as follows: suppose that the result      |
   |           | formatted with presentation type "'e'" and precision "p-1" |
   |           | would have exponent "exp".  Then if "-4 <= exp < p", the   |
   |           | number is formatted with presentation type "'f'" and       |
   |           | precision "p-1-exp".  Otherwise, the number is formatted   |
   |           | with presentation type "'e'" and precision "p-1". In both  |
   |           | cases insignificant trailing zeros are removed from the    |
   |           | significand, and the decimal point is also removed if      |
   |           | there are no remaining digits following it.  Positive and  |
   |           | negative infinity, positive and negative zero, and nans,   |
   |           | are formatted as "inf", "-inf", "0", "-0" and "nan"        |
   |           | respectively, regardless of the precision.  A precision of |
   |           | "0" is treated as equivalent to a precision of "1". The    |
   |           | default precision is "6".                                  |
   +-----------+------------------------------------------------------------+
   | "'G'"     | General format. Same as "'g'" except switches to "'E'" if  |
   |           | the number gets too large. The representations of infinity |
   |           | and NaN are uppercased, too.                               |
   +-----------+------------------------------------------------------------+
   | "'n'"     | Number. This is the same as "'g'", except that it uses the |
   |           | current locale setting to insert the appropriate number    |
   |           | separator characters.                                      |
   +-----------+------------------------------------------------------------+
   | "'%'"     | Percentage. Multiplies the number by 100 and displays in   |
   |           | fixed ("'f'") format, followed by a percent sign.          |
   +-----------+------------------------------------------------------------+
   | None      | Similar to "'g'", except that fixed-point notation, when   |
   |           | used, has at least one digit past the decimal point. The   |
   |           | default precision is as high as needed to represent the    |
   |           | particular value. The overall effect is to match the       |
   |           | output of "str()" as altered by the other format           |
   |           | modifiers.                                                 |
   +-----------+------------------------------------------------------------+


Format examples
===============

This section contains examples of the "str.format()" syntax and
comparison with the old "%"-formatting.

In most of the cases the syntax is similar to the old "%"-formatting,
with the addition of the "{}" and with ":" used instead of "%". For
example, "'%03.2f'" can be translated to "'{:03.2f}'".

The new format syntax also supports new and different options, shown
in the follow examples.

Accessing arguments by position:

   >>> '{0}, {1}, {2}'.format('a', 'b', 'c')
   'a, b, c'
   >>> '{}, {}, {}'.format('a', 'b', 'c')  # 3.1+ only
   'a, b, c'
   >>> '{2}, {1}, {0}'.format('a', 'b', 'c')
   'c, b, a'
   >>> '{2}, {1}, {0}'.format(*'abc')      # unpacking argument sequence
   'c, b, a'
   >>> '{0}{1}{0}'.format('abra', 'cad')   # arguments' indices can be repeated
   'abracadabra'

Accessing arguments by name:

   >>> 'Coordinates: {latitude}, {longitude}'.format(latitude='37.24N', longitude='-115.81W')
   'Coordinates: 37.24N, -115.81W'
   >>> coord = {'latitude': '37.24N', 'longitude': '-115.81W'}
   >>> 'Coordinates: {latitude}, {longitude}'.format(**coord)
   'Coordinates: 37.24N, -115.81W'

Accessing arguments' attributes:

   >>> c = 3-5j
   >>> ('The complex number {0} is formed from the real part {0.real} '
   ...  'and the imaginary part {0.imag}.').format(c)
   'The complex number (3-5j) is formed from the real part 3.0 and the imaginary part -5.0.'
   >>> class Point:
   ...     def __init__(self, x, y):
   ...         self.x, self.y = x, y
   ...     def __str__(self):
   ...         return 'Point({self.x}, {self.y})'.format(self=self)
   ...
   >>> str(Point(4, 2))
   'Point(4, 2)'

Accessing arguments' items:

   >>> coord = (3, 5)
   >>> 'X: {0[0]};  Y: {0[1]}'.format(coord)
   'X: 3;  Y: 5'

Replacing "%s" and "%r":

   >>> "repr() shows quotes: {!r}; str() doesn't: {!s}".format('test1', 'test2')
   "repr() shows quotes: 'test1'; str() doesn't: test2"

Aligning the text and specifying a width:

   >>> '{:<30}'.format('left aligned')
   'left aligned                  '
   >>> '{:>30}'.format('right aligned')
   '                 right aligned'
   >>> '{:^30}'.format('centered')
   '           centered           '
   >>> '{:*^30}'.format('centered')  # use '*' as a fill char
   '***********centered***********'

Replacing "%+f", "%-f", and "% f" and specifying a sign:

   >>> '{:+f}; {:+f}'.format(3.14, -3.14)  # show it always
   '+3.140000; -3.140000'
   >>> '{: f}; {: f}'.format(3.14, -3.14)  # show a space for positive numbers
   ' 3.140000; -3.140000'
   >>> '{:-f}; {:-f}'.format(3.14, -3.14)  # show only the minus -- same as '{:f}; {:f}'
   '3.140000; -3.140000'

Replacing "%x" and "%o" and converting the value to different bases:

   >>> # format also supports binary numbers
   >>> "int: {0:d};  hex: {0:x};  oct: {0:o};  bin: {0:b}".format(42)
   'int: 42;  hex: 2a;  oct: 52;  bin: 101010'
   >>> # with 0x, 0o, or 0b as prefix:
   >>> "int: {0:d};  hex: {0:#x};  oct: {0:#o};  bin: {0:#b}".format(42)
   'int: 42;  hex: 0x2a;  oct: 0o52;  bin: 0b101010'

Using the comma as a thousands separator:

   >>> '{:,}'.format(1234567890)
   '1,234,567,890'

Expressing a percentage:

   >>> points = 19
   >>> total = 22
   >>> 'Correct answers: {:.2%}'.format(points/total)
   'Correct answers: 86.36%'

Using type-specific formatting:

   >>> import datetime
   >>> d = datetime.datetime(2010, 7, 4, 12, 15, 58)
   >>> '{:%Y-%m-%d %H:%M:%S}'.format(d)
   '2010-07-04 12:15:58'

Nesting arguments and more complex examples:

   >>> for align, text in zip('<^>', ['left', 'center', 'right']):
   ...     '{0:{fill}{align}16}'.format(text, fill=align, align=align)
   ...
   'left<<<<<<<<<<<<'
   '^^^^^center^^^^^'
   '>>>>>>>>>>>right'
   >>>
   >>> octets = [192, 168, 0, 1]
   >>> '{:02X}{:02X}{:02X}{:02X}'.format(*octets)
   'C0A80001'
   >>> int(_, 16)
   3232235521
   >>>
   >>> width = 5
   >>> for num in range(5,12): #doctest: +NORMALIZE_WHITESPACE
   ...     for base in 'dXob':
   ...         print('{0:{width}{base}}'.format(num, base=base, width=width), end=' ')
   ...     print()
   ...
       5     5     5   101
       6     6     6   110
       7     7     7   111
       8     8    10  1000
       9     9    11  1001
      10     A    12  1010
      11     B    13  1011
"""
    , 'function':
    """Function definitions
********************

A function definition defines a user-defined function object (see
section The standard type hierarchy):

   funcdef                 ::= [decorators] "def" funcname "(" [parameter_list] ")" ["->" expression] ":" suite
   decorators              ::= decorator+
   decorator               ::= "@" dotted_name ["(" [argument_list [","]] ")"] NEWLINE
   dotted_name             ::= identifier ("." identifier)*
   parameter_list          ::= defparameter ("," defparameter)* ["," [parameter_list_starargs]]
                      | parameter_list_starargs
   parameter_list_starargs ::= "*" [parameter] ("," defparameter)* ["," ["**" parameter [","]]]
                               | "**" parameter [","]
   parameter               ::= identifier [":" expression]
   defparameter            ::= parameter ["=" expression]
   funcname                ::= identifier

A function definition is an executable statement.  Its execution binds
the function name in the current local namespace to a function object
(a wrapper around the executable code for the function).  This
function object contains a reference to the current global namespace
as the global namespace to be used when the function is called.

The function definition does not execute the function body; this gets
executed only when the function is called. [3]

A function definition may be wrapped by one or more *decorator*
expressions. Decorator expressions are evaluated when the function is
defined, in the scope that contains the function definition.  The
result must be a callable, which is invoked with the function object
as the only argument. The returned value is bound to the function name
instead of the function object.  Multiple decorators are applied in
nested fashion. For example, the following code

   @f1(arg)
   @f2
   def func(): pass

is roughly equivalent to

   def func(): pass
   func = f1(arg)(f2(func))

except that the original function is not temporarily bound to the name
"func".

When one or more *parameters* have the form *parameter* "="
*expression*, the function is said to have "default parameter values."
For a parameter with a default value, the corresponding *argument* may
be omitted from a call, in which case the parameter's default value is
substituted.  If a parameter has a default value, all following
parameters up until the ""*"" must also have a default value --- this
is a syntactic restriction that is not expressed by the grammar.

**Default parameter values are evaluated from left to right when the
function definition is executed.** This means that the expression is
evaluated once, when the function is defined, and that the same "pre-
computed" value is used for each call.  This is especially important
to understand when a default parameter is a mutable object, such as a
list or a dictionary: if the function modifies the object (e.g. by
appending an item to a list), the default value is in effect modified.
This is generally not what was intended.  A way around this is to use
"None" as the default, and explicitly test for it in the body of the
function, e.g.:

   def whats_on_the_telly(penguin=None):
       if penguin is None:
           penguin = []
       penguin.append("property of the zoo")
       return penguin

Function call semantics are described in more detail in section Calls.
A function call always assigns values to all parameters mentioned in
the parameter list, either from position arguments, from keyword
arguments, or from default values.  If the form ""*identifier"" is
present, it is initialized to a tuple receiving any excess positional
parameters, defaulting to the empty tuple. If the form
""**identifier"" is present, it is initialized to a new ordered
mapping receiving any excess keyword arguments, defaulting to a new
empty mapping of the same type.  Parameters after ""*"" or
""*identifier"" are keyword-only parameters and may only be passed
used keyword arguments.

Parameters may have annotations of the form "": expression"" following
the parameter name.  Any parameter may have an annotation even those
of the form "*identifier" or "**identifier".  Functions may have
"return" annotation of the form ""-> expression"" after the parameter
list.  These annotations can be any valid Python expression and are
evaluated when the function definition is executed.  Annotations may
be evaluated in a different order than they appear in the source code.
The presence of annotations does not change the semantics of a
function.  The annotation values are available as values of a
dictionary keyed by the parameters' names in the "__annotations__"
attribute of the function object.

It is also possible to create anonymous functions (functions not bound
to a name), for immediate use in expressions.  This uses lambda
expressions, described in section Lambdas.  Note that the lambda
expression is merely a shorthand for a simplified function definition;
a function defined in a ""def"" statement can be passed around or
assigned to another name just like a function defined by a lambda
expression.  The ""def"" form is actually more powerful since it
allows the execution of multiple statements and annotations.

**Programmer's note:** Functions are first-class objects.  A ""def""
statement executed inside a function definition defines a local
function that can be returned or passed around.  Free variables used
in the nested function can access the local variables of the function
containing the def.  See section Naming and binding for details.

See also:

  **PEP 3107** - Function Annotations
     The original specification for function annotations.
"""
    , 'global':
    """The "global" statement
**********************

   global_stmt ::= "global" identifier ("," identifier)*

The "global" statement is a declaration which holds for the entire
current code block.  It means that the listed identifiers are to be
interpreted as globals.  It would be impossible to assign to a global
variable without "global", although free variables may refer to
globals without being declared global.

Names listed in a "global" statement must not be used in the same code
block textually preceding that "global" statement.

Names listed in a "global" statement must not be defined as formal
parameters or in a "for" loop control target, "class" definition,
function definition, "import" statement, or variable annotation.

**CPython implementation detail:** The current implementation does not
enforce some of these restriction, but programs should not abuse this
freedom, as future implementations may enforce them or silently change
the meaning of the program.

**Programmer's note:** "global" is a directive to the parser.  It
applies only to code parsed at the same time as the "global"
statement. In particular, a "global" statement contained in a string
or code object supplied to the built-in "exec()" function does not
affect the code block *containing* the function call, and code
contained in such a string is unaffected by "global" statements in the
code containing the function call.  The same applies to the "eval()"
and "compile()" functions.
"""
    , 'id-classes':
    """Reserved classes of identifiers
*******************************

Certain classes of identifiers (besides keywords) have special
meanings.  These classes are identified by the patterns of leading and
trailing underscore characters:

"_*"
   Not imported by "from module import *".  The special identifier "_"
   is used in the interactive interpreter to store the result of the
   last evaluation; it is stored in the "builtins" module.  When not
   in interactive mode, "_" has no special meaning and is not defined.
   See section The import statement.

   Note: The name "_" is often used in conjunction with
     internationalization; refer to the documentation for the
     "gettext" module for more information on this convention.

"__*__"
   System-defined names. These names are defined by the interpreter
   and its implementation (including the standard library).  Current
   system names are discussed in the Special method names section and
   elsewhere.  More will likely be defined in future versions of
   Python.  *Any* use of "__*__" names, in any context, that does not
   follow explicitly documented use, is subject to breakage without
   warning.

"__*"
   Class-private names.  Names in this category, when used within the
   context of a class definition, are re-written to use a mangled form
   to help avoid name clashes between "private" attributes of base and
   derived classes. See section Identifiers (Names).
"""
    , 'identifiers':
    """Identifiers and keywords
************************

Identifiers (also referred to as *names*) are described by the
following lexical definitions.

The syntax of identifiers in Python is based on the Unicode standard
annex UAX-31, with elaboration and changes as defined below; see also
**PEP 3131** for further details.

Within the ASCII range (U+0001..U+007F), the valid characters for
identifiers are the same as in Python 2.x: the uppercase and lowercase
letters "A" through "Z", the underscore "_" and, except for the first
character, the digits "0" through "9".

Python 3.0 introduces additional characters from outside the ASCII
range (see **PEP 3131**).  For these characters, the classification
uses the version of the Unicode Character Database as included in the
"unicodedata" module.

Identifiers are unlimited in length.  Case is significant.

   identifier   ::= xid_start xid_continue*
   id_start     ::= <all characters in general categories Lu, Ll, Lt, Lm, Lo, Nl, the underscore, and characters with the Other_ID_Start property>
   id_continue  ::= <all characters in id_start, plus characters in the categories Mn, Mc, Nd, Pc and others with the Other_ID_Continue property>
   xid_start    ::= <all characters in id_start whose NFKC normalization is in "id_start xid_continue*">
   xid_continue ::= <all characters in id_continue whose NFKC normalization is in "id_continue*">

The Unicode category codes mentioned above stand for:

* *Lu* - uppercase letters

* *Ll* - lowercase letters

* *Lt* - titlecase letters

* *Lm* - modifier letters

* *Lo* - other letters

* *Nl* - letter numbers

* *Mn* - nonspacing marks

* *Mc* - spacing combining marks

* *Nd* - decimal numbers

* *Pc* - connector punctuations

* *Other_ID_Start* - explicit list of characters in PropList.txt to
  support backwards compatibility

* *Other_ID_Continue* - likewise

All identifiers are converted into the normal form NFKC while parsing;
comparison of identifiers is based on NFKC.

A non-normative HTML file listing all valid identifier characters for
Unicode 4.1 can be found at https://www.dcl.hpi.uni-
potsdam.de/home/loewis/table-3131.html.


Keywords
========

The following identifiers are used as reserved words, or *keywords* of
the language, and cannot be used as ordinary identifiers.  They must
be spelled exactly as written here:

   False      class      finally    is         return
   None       continue   for        lambda     try
   True       def        from       nonlocal   while
   and        del        global     not        with
   as         elif       if         or         yield
   assert     else       import     pass
   break      except     in         raise


Reserved classes of identifiers
===============================

Certain classes of identifiers (besides keywords) have special
meanings.  These classes are identified by the patterns of leading and
trailing underscore characters:

"_*"
   Not imported by "from module import *".  The special identifier "_"
   is used in the interactive interpreter to store the result of the
   last evaluation; it is stored in the "builtins" module.  When not
   in interactive mode, "_" has no special meaning and is not defined.
   See section The import statement.

   Note: The name "_" is often used in conjunction with
     internationalization; refer to the documentation for the
     "gettext" module for more information on this convention.

"__*__"
   System-defined names. These names are defined by the interpreter
   and its implementation (including the standard library).  Current
   system names are discussed in the Special method names section and
   elsewhere.  More will likely be defined in future versions of
   Python.  *Any* use of "__*__" names, in any context, that does not
   follow explicitly documented use, is subject to breakage without
   warning.

"__*"
   Class-private names.  Names in this category, when used within the
   context of a class definition, are re-written to use a mangled form
   to help avoid name clashes between "private" attributes of base and
   derived classes. See section Identifiers (Names).
"""
    , 'if':
    """The "if" statement
******************

The "if" statement is used for conditional execution:

   if_stmt ::= "if" expression ":" suite
               ( "elif" expression ":" suite )*
               ["else" ":" suite]

It selects exactly one of the suites by evaluating the expressions one
by one until one is found to be true (see section Boolean operations
for the definition of true and false); then that suite is executed
(and no other part of the "if" statement is executed or evaluated).
If all expressions are false, the suite of the "else" clause, if
present, is executed.
"""
    , 'imaginary':
    """Imaginary literals
******************

Imaginary literals are described by the following lexical definitions:

   imagnumber ::= (floatnumber | digitpart) ("j" | "J")

An imaginary literal yields a complex number with a real part of 0.0.
Complex numbers are represented as a pair of floating point numbers
and have the same restrictions on their range.  To create a complex
number with a nonzero real part, add a floating point number to it,
e.g., "(3+4j)".  Some examples of imaginary literals:

   3.14j   10.j    10j     .001j   1e100j   3.14e-10j   3.14_15_93j
"""
    , 'import':
    """The "import" statement
**********************

   import_stmt     ::= "import" module ["as" name] ( "," module ["as" name] )*
                   | "from" relative_module "import" identifier ["as" name]
                   ( "," identifier ["as" name] )*
                   | "from" relative_module "import" "(" identifier ["as" name]
                   ( "," identifier ["as" name] )* [","] ")"
                   | "from" module "import" "*"
   module          ::= (identifier ".")* identifier
   relative_module ::= "."* module | "."+
   name            ::= identifier

The basic import statement (no "from" clause) is executed in two
steps:

1. find a module, loading and initializing it if necessary

2. define a name or names in the local namespace for the scope
   where the "import" statement occurs.

When the statement contains multiple clauses (separated by commas) the
two steps are carried out separately for each clause, just as though
the clauses had been separated out into individual import statements.

The details of the first step, finding and loading modules are
described in greater detail in the section on the import system, which
also describes the various types of packages and modules that can be
imported, as well as all the hooks that can be used to customize the
import system. Note that failures in this step may indicate either
that the module could not be located, *or* that an error occurred
while initializing the module, which includes execution of the
module's code.

If the requested module is retrieved successfully, it will be made
available in the local namespace in one of three ways:

* If the module name is followed by "as", then the name following
  "as" is bound directly to the imported module.

* If no other name is specified, and the module being imported is a
  top level module, the module's name is bound in the local namespace
  as a reference to the imported module

* If the module being imported is *not* a top level module, then the
  name of the top level package that contains the module is bound in
  the local namespace as a reference to the top level package. The
  imported module must be accessed using its full qualified name
  rather than directly

The "from" form uses a slightly more complex process:

1. find the module specified in the "from" clause, loading and
   initializing it if necessary;

2. for each of the identifiers specified in the "import" clauses:

   1. check if the imported module has an attribute by that name

   2. if not, attempt to import a submodule with that name and then
      check the imported module again for that attribute

   3. if the attribute is not found, "ImportError" is raised.

   4. otherwise, a reference to that value is stored in the local
      namespace, using the name in the "as" clause if it is present,
      otherwise using the attribute name

Examples:

   import foo                 # foo imported and bound locally
   import foo.bar.baz         # foo.bar.baz imported, foo bound locally
   import foo.bar.baz as fbb  # foo.bar.baz imported and bound as fbb
   from foo.bar import baz    # foo.bar.baz imported and bound as baz
   from foo import attr       # foo imported and foo.attr bound as attr

If the list of identifiers is replaced by a star ("'*'"), all public
names defined in the module are bound in the local namespace for the
scope where the "import" statement occurs.

The *public names* defined by a module are determined by checking the
module's namespace for a variable named "__all__"; if defined, it must
be a sequence of strings which are names defined or imported by that
module.  The names given in "__all__" are all considered public and
are required to exist.  If "__all__" is not defined, the set of public
names includes all names found in the module's namespace which do not
begin with an underscore character ("'_'").  "__all__" should contain
the entire public API. It is intended to avoid accidentally exporting
items that are not part of the API (such as library modules which were
imported and used within the module).

The wild card form of import --- "from module import *" --- is only
allowed at the module level.  Attempting to use it in class or
function definitions will raise a "SyntaxError".

When specifying what module to import you do not have to specify the
absolute name of the module. When a module or package is contained
within another package it is possible to make a relative import within
the same top package without having to mention the package name. By
using leading dots in the specified module or package after "from" you
can specify how high to traverse up the current package hierarchy
without specifying exact names. One leading dot means the current
package where the module making the import exists. Two dots means up
one package level. Three dots is up two levels, etc. So if you execute
"from . import mod" from a module in the "pkg" package then you will
end up importing "pkg.mod". If you execute "from ..subpkg2 import mod"
from within "pkg.subpkg1" you will import "pkg.subpkg2.mod". The
specification for relative imports is contained within **PEP 328**.

"importlib.import_module()" is provided to support applications that
determine dynamically the modules to be loaded.


Future statements
=================

A *future statement* is a directive to the compiler that a particular
module should be compiled using syntax or semantics that will be
available in a specified future release of Python where the feature
becomes standard.

The future statement is intended to ease migration to future versions
of Python that introduce incompatible changes to the language.  It
allows use of the new features on a per-module basis before the
release in which the feature becomes standard.

   future_statement ::= "from" "__future__" "import" feature ["as" name]
                        ("," feature ["as" name])*
                        | "from" "__future__" "import" "(" feature ["as" name]
                        ("," feature ["as" name])* [","] ")"
   feature          ::= identifier
   name             ::= identifier

A future statement must appear near the top of the module.  The only
lines that can appear before a future statement are:

* the module docstring (if any),

* comments,

* blank lines, and

* other future statements.

The features recognized by Python 3.0 are "absolute_import",
"division", "generators", "unicode_literals", "print_function",
"nested_scopes" and "with_statement".  They are all redundant because
they are always enabled, and only kept for backwards compatibility.

A future statement is recognized and treated specially at compile
time: Changes to the semantics of core constructs are often
implemented by generating different code.  It may even be the case
that a new feature introduces new incompatible syntax (such as a new
reserved word), in which case the compiler may need to parse the
module differently.  Such decisions cannot be pushed off until
runtime.

For any given release, the compiler knows which feature names have
been defined, and raises a compile-time error if a future statement
contains a feature not known to it.

The direct runtime semantics are the same as for any import statement:
there is a standard module "__future__", described later, and it will
be imported in the usual way at the time the future statement is
executed.

The interesting runtime semantics depend on the specific feature
enabled by the future statement.

Note that there is nothing special about the statement:

   import __future__ [as name]

That is not a future statement; it's an ordinary import statement with
no special semantics or syntax restrictions.

Code compiled by calls to the built-in functions "exec()" and
"compile()" that occur in a module "M" containing a future statement
will, by default, use the new syntax or semantics associated with the
future statement.  This can be controlled by optional arguments to
"compile()" --- see the documentation of that function for details.

A future statement typed at an interactive interpreter prompt will
take effect for the rest of the interpreter session.  If an
interpreter is started with the "-i" option, is passed a script name
to execute, and the script includes a future statement, it will be in
effect in the interactive session started after the script is
executed.

See also:

  **PEP 236** - Back to the __future__
     The original proposal for the __future__ mechanism.
"""
    , 'in':
    """Membership test operations
**************************

The operators "in" and "not in" test for membership.  "x in s"
evaluates to "True" if *x* is a member of *s*, and "False" otherwise.
"x not in s" returns the negation of "x in s".  All built-in sequences
and set types support this as well as dictionary, for which "in" tests
whether the dictionary has a given key. For container types such as
list, tuple, set, frozenset, dict, or collections.deque, the
expression "x in y" is equivalent to "any(x is e or x == e for e in
y)".

For the string and bytes types, "x in y" is "True" if and only if *x*
is a substring of *y*.  An equivalent test is "y.find(x) != -1".
Empty strings are always considered to be a substring of any other
string, so ""\" in "abc"" will return "True".

For user-defined classes which define the "__contains__()" method, "x
in y" returns "True" if "y.__contains__(x)" returns a true value, and
"False" otherwise.

For user-defined classes which do not define "__contains__()" but do
define "__iter__()", "x in y" is "True" if some value "z" with "x ==
z" is produced while iterating over "y".  If an exception is raised
during the iteration, it is as if "in" raised that exception.

Lastly, the old-style iteration protocol is tried: if a class defines
"__getitem__()", "x in y" is "True" if and only if there is a non-
negative integer index *i* such that "x == y[i]", and all lower
integer indices do not raise "IndexError" exception.  (If any other
exception is raised, it is as if "in" raised that exception).

The operator "not in" is defined to have the inverse true value of
"in".
"""
    , 'integers':
    """Integer literals
****************

Integer literals are described by the following lexical definitions:

   integer      ::= decinteger | bininteger | octinteger | hexinteger
   decinteger   ::= nonzerodigit (["_"] digit)* | "0"+ (["_"] "0")*
   bininteger   ::= "0" ("b" | "B") (["_"] bindigit)+
   octinteger   ::= "0" ("o" | "O") (["_"] octdigit)+
   hexinteger   ::= "0" ("x" | "X") (["_"] hexdigit)+
   nonzerodigit ::= "1"..."9"
   digit        ::= "0"..."9"
   bindigit     ::= "0" | "1"
   octdigit     ::= "0"..."7"
   hexdigit     ::= digit | "a"..."f" | "A"..."F"

There is no limit for the length of integer literals apart from what
can be stored in available memory.

Underscores are ignored for determining the numeric value of the
literal.  They can be used to group digits for enhanced readability.
One underscore can occur between digits, and after base specifiers
like "0x".

Note that leading zeros in a non-zero decimal number are not allowed.
This is for disambiguation with C-style octal literals, which Python
used before version 3.0.

Some examples of integer literals:

   7     2147483647                        0o177    0b100110111
   3     79228162514264337593543950336     0o377    0xdeadbeef
         100_000_000_000                   0b_1110_0101

Changed in version 3.6: Underscores are now allowed for grouping
purposes in literals.
"""
    , 'lambda':
    """Lambdas
*******

   lambda_expr        ::= "lambda" [parameter_list]: expression
   lambda_expr_nocond ::= "lambda" [parameter_list]: expression_nocond

Lambda expressions (sometimes called lambda forms) are used to create
anonymous functions. The expression "lambda arguments: expression"
yields a function object.  The unnamed object behaves like a function
object defined with:

   def <lambda>(arguments):
       return expression

See section Function definitions for the syntax of parameter lists.
Note that functions created with lambda expressions cannot contain
statements or annotations.
"""
    , 'lists':
    """List displays
*************

A list display is a possibly empty series of expressions enclosed in
square brackets:

   list_display ::= "[" [starred_list | comprehension] "]"

A list display yields a new list object, the contents being specified
by either a list of expressions or a comprehension.  When a comma-
separated list of expressions is supplied, its elements are evaluated
from left to right and placed into the list object in that order.
When a comprehension is supplied, the list is constructed from the
elements resulting from the comprehension.
"""
    , 'naming':
    """Naming and binding
******************


Binding of names
================

*Names* refer to objects.  Names are introduced by name binding
operations.

The following constructs bind names: formal parameters to functions,
"import" statements, class and function definitions (these bind the
class or function name in the defining block), and targets that are
identifiers if occurring in an assignment, "for" loop header, or after
"as" in a "with" statement or "except" clause. The "import" statement
of the form "from ... import *" binds all names defined in the
imported module, except those beginning with an underscore.  This form
may only be used at the module level.

A target occurring in a "del" statement is also considered bound for
this purpose (though the actual semantics are to unbind the name).

Each assignment or import statement occurs within a block defined by a
class or function definition or at the module level (the top-level
code block).

If a name is bound in a block, it is a local variable of that block,
unless declared as "nonlocal" or "global".  If a name is bound at the
module level, it is a global variable.  (The variables of the module
code block are local and global.)  If a variable is used in a code
block but not defined there, it is a *free variable*.

Each occurrence of a name in the program text refers to the *binding*
of that name established by the following name resolution rules.


Resolution of names
===================

A *scope* defines the visibility of a name within a block.  If a local
variable is defined in a block, its scope includes that block.  If the
definition occurs in a function block, the scope extends to any blocks
contained within the defining one, unless a contained block introduces
a different binding for the name.

When a name is used in a code block, it is resolved using the nearest
enclosing scope.  The set of all such scopes visible to a code block
is called the block's *environment*.

When a name is not found at all, a "NameError" exception is raised. If
the current scope is a function scope, and the name refers to a local
variable that has not yet been bound to a value at the point where the
name is used, an "UnboundLocalError" exception is raised.
"UnboundLocalError" is a subclass of "NameError".

If a name binding operation occurs anywhere within a code block, all
uses of the name within the block are treated as references to the
current block.  This can lead to errors when a name is used within a
block before it is bound.  This rule is subtle.  Python lacks
declarations and allows name binding operations to occur anywhere
within a code block.  The local variables of a code block can be
determined by scanning the entire text of the block for name binding
operations.

If the "global" statement occurs within a block, all uses of the name
specified in the statement refer to the binding of that name in the
top-level namespace.  Names are resolved in the top-level namespace by
searching the global namespace, i.e. the namespace of the module
containing the code block, and the builtins namespace, the namespace
of the module "builtins".  The global namespace is searched first.  If
the name is not found there, the builtins namespace is searched.  The
"global" statement must precede all uses of the name.

The "global" statement has the same scope as a name binding operation
in the same block.  If the nearest enclosing scope for a free variable
contains a global statement, the free variable is treated as a global.

The "nonlocal" statement causes corresponding names to refer to
previously bound variables in the nearest enclosing function scope.
"SyntaxError" is raised at compile time if the given name does not
exist in any enclosing function scope.

The namespace for a module is automatically created the first time a
module is imported.  The main module for a script is always called
"__main__".

Class definition blocks and arguments to "exec()" and "eval()" are
special in the context of name resolution. A class definition is an
executable statement that may use and define names. These references
follow the normal rules for name resolution with an exception that
unbound local variables are looked up in the global namespace. The
namespace of the class definition becomes the attribute dictionary of
the class. The scope of names defined in a class block is limited to
the class block; it does not extend to the code blocks of methods --
this includes comprehensions and generator expressions since they are
implemented using a function scope.  This means that the following
will fail:

   class A:
       a = 42
       b = list(a + i for i in range(10))


Builtins and restricted execution
=================================

**CPython implementation detail:** Users should not touch
"__builtins__"; it is strictly an implementation detail.  Users
wanting to override values in the builtins namespace should "import"
the "builtins" module and modify its attributes appropriately.

The builtins namespace associated with the execution of a code block
is actually found by looking up the name "__builtins__" in its global
namespace; this should be a dictionary or a module (in the latter case
the module's dictionary is used).  By default, when in the "__main__"
module, "__builtins__" is the built-in module "builtins"; when in any
other module, "__builtins__" is an alias for the dictionary of the
"builtins" module itself.


Interaction with dynamic features
=================================

Name resolution of free variables occurs at runtime, not at compile
time. This means that the following code will print 42:

   i = 10
   def f():
       print(i)
   i = 42
   f()

The "eval()" and "exec()" functions do not have access to the full
environment for resolving names.  Names may be resolved in the local
and global namespaces of the caller.  Free variables are not resolved
in the nearest enclosing namespace, but in the global namespace.  [1]
The "exec()" and "eval()" functions have optional arguments to
override the global and local namespace.  If only one namespace is
specified, it is used for both.
"""
    , 'nonlocal':
    """The "nonlocal" statement
************************

   nonlocal_stmt ::= "nonlocal" identifier ("," identifier)*

The "nonlocal" statement causes the listed identifiers to refer to
previously bound variables in the nearest enclosing scope excluding
globals. This is important because the default behavior for binding is
to search the local namespace first.  The statement allows
encapsulated code to rebind variables outside of the local scope
besides the global (module) scope.

Names listed in a "nonlocal" statement, unlike those listed in a
"global" statement, must refer to pre-existing bindings in an
enclosing scope (the scope in which a new binding should be created
cannot be determined unambiguously).

Names listed in a "nonlocal" statement must not collide with pre-
existing bindings in the local scope.

See also:

  **PEP 3104** - Access to Names in Outer Scopes
     The specification for the "nonlocal" statement.
"""
    , 'numbers':
    """Numeric literals
****************

There are three types of numeric literals: integers, floating point
numbers, and imaginary numbers.  There are no complex literals
(complex numbers can be formed by adding a real number and an
imaginary number).

Note that numeric literals do not include a sign; a phrase like "-1"
is actually an expression composed of the unary operator '"-"' and the
literal "1".
"""
    , 'numeric-types':
    """Emulating numeric types
***********************

The following methods can be defined to emulate numeric objects.
Methods corresponding to operations that are not supported by the
particular kind of number implemented (e.g., bitwise operations for
non-integral numbers) should be left undefined.

object.__add__(self, other)
object.__sub__(self, other)
object.__mul__(self, other)
object.__matmul__(self, other)
object.__truediv__(self, other)
object.__floordiv__(self, other)
object.__mod__(self, other)
object.__divmod__(self, other)
object.__pow__(self, other[, modulo])
object.__lshift__(self, other)
object.__rshift__(self, other)
object.__and__(self, other)
object.__xor__(self, other)
object.__or__(self, other)

   These methods are called to implement the binary arithmetic
   operations ("+", "-", "*", "@", "/", "//", "%", "divmod()",
   "pow()", "**", "<<", ">>", "&", "^", "|").  For instance, to
   evaluate the expression "x + y", where *x* is an instance of a
   class that has an "__add__()" method, "x.__add__(y)" is called.
   The "__divmod__()" method should be the equivalent to using
   "__floordiv__()" and "__mod__()"; it should not be related to
   "__truediv__()".  Note that "__pow__()" should be defined to accept
   an optional third argument if the ternary version of the built-in
   "pow()" function is to be supported.

   If one of those methods does not support the operation with the
   supplied arguments, it should return "NotImplemented".

object.__radd__(self, other)
object.__rsub__(self, other)
object.__rmul__(self, other)
object.__rmatmul__(self, other)
object.__rtruediv__(self, other)
object.__rfloordiv__(self, other)
object.__rmod__(self, other)
object.__rdivmod__(self, other)
object.__rpow__(self, other)
object.__rlshift__(self, other)
object.__rrshift__(self, other)
object.__rand__(self, other)
object.__rxor__(self, other)
object.__ror__(self, other)

   These methods are called to implement the binary arithmetic
   operations ("+", "-", "*", "@", "/", "//", "%", "divmod()",
   "pow()", "**", "<<", ">>", "&", "^", "|") with reflected (swapped)
   operands.  These functions are only called if the left operand does
   not support the corresponding operation [3] and the operands are of
   different types. [4] For instance, to evaluate the expression "x -
   y", where *y* is an instance of a class that has an "__rsub__()"
   method, "y.__rsub__(x)" is called if "x.__sub__(y)" returns
   *NotImplemented*.

   Note that ternary "pow()" will not try calling "__rpow__()" (the
   coercion rules would become too complicated).

   Note: If the right operand's type is a subclass of the left
     operand's type and that subclass provides the reflected method
     for the operation, this method will be called before the left
     operand's non-reflected method.  This behavior allows subclasses
     to override their ancestors' operations.

object.__iadd__(self, other)
object.__isub__(self, other)
object.__imul__(self, other)
object.__imatmul__(self, other)
object.__itruediv__(self, other)
object.__ifloordiv__(self, other)
object.__imod__(self, other)
object.__ipow__(self, other[, modulo])
object.__ilshift__(self, other)
object.__irshift__(self, other)
object.__iand__(self, other)
object.__ixor__(self, other)
object.__ior__(self, other)

   These methods are called to implement the augmented arithmetic
   assignments ("+=", "-=", "*=", "@=", "/=", "//=", "%=", "**=",
   "<<=", ">>=", "&=", "^=", "|=").  These methods should attempt to
   do the operation in-place (modifying *self*) and return the result
   (which could be, but does not have to be, *self*).  If a specific
   method is not defined, the augmented assignment falls back to the
   normal methods.  For instance, if *x* is an instance of a class
   with an "__iadd__()" method, "x += y" is equivalent to "x =
   x.__iadd__(y)" . Otherwise, "x.__add__(y)" and "y.__radd__(x)" are
   considered, as with the evaluation of "x + y". In certain
   situations, augmented assignment can result in unexpected errors
   (see Why does a_tuple[i] += ['item'] raise an exception when the
   addition works?), but this behavior is in fact part of the data
   model.

object.__neg__(self)
object.__pos__(self)
object.__abs__(self)
object.__invert__(self)

   Called to implement the unary arithmetic operations ("-", "+",
   "abs()" and "~").

object.__complex__(self)
object.__int__(self)
object.__float__(self)
object.__round__(self[, n])

   Called to implement the built-in functions "complex()", "int()",
   "float()" and "round()".  Should return a value of the appropriate
   type.

object.__index__(self)

   Called to implement "operator.index()", and whenever Python needs
   to losslessly convert the numeric object to an integer object (such
   as in slicing, or in the built-in "bin()", "hex()" and "oct()"
   functions). Presence of this method indicates that the numeric
   object is an integer type.  Must return an integer.

   Note: In order to have a coherent integer type class, when
     "__index__()" is defined "__int__()" should also be defined, and
     both should return the same value.
"""
    , 'objects':
    """Objects, values and types
*************************

*Objects* are Python's abstraction for data.  All data in a Python
program is represented by objects or by relations between objects. (In
a sense, and in conformance to Von Neumann's model of a "stored
program computer," code is also represented by objects.)

Every object has an identity, a type and a value.  An object's
*identity* never changes once it has been created; you may think of it
as the object's address in memory.  The '"is"' operator compares the
identity of two objects; the "id()" function returns an integer
representing its identity.

**CPython implementation detail:** For CPython, "id(x)" is the memory
address where "x" is stored.

An object's type determines the operations that the object supports
(e.g., "does it have a length?") and also defines the possible values
for objects of that type.  The "type()" function returns an object's
type (which is an object itself).  Like its identity, an object's
*type* is also unchangeable. [1]

The *value* of some objects can change.  Objects whose value can
change are said to be *mutable*; objects whose value is unchangeable
once they are created are called *immutable*. (The value of an
immutable container object that contains a reference to a mutable
object can change when the latter's value is changed; however the
container is still considered immutable, because the collection of
objects it contains cannot be changed.  So, immutability is not
strictly the same as having an unchangeable value, it is more subtle.)
An object's mutability is determined by its type; for instance,
numbers, strings and tuples are immutable, while dictionaries and
lists are mutable.

Objects are never explicitly destroyed; however, when they become
unreachable they may be garbage-collected.  An implementation is
allowed to postpone garbage collection or omit it altogether --- it is
a matter of implementation quality how garbage collection is
implemented, as long as no objects are collected that are still
reachable.

**CPython implementation detail:** CPython currently uses a reference-
counting scheme with (optional) delayed detection of cyclically linked
garbage, which collects most objects as soon as they become
unreachable, but is not guaranteed to collect garbage containing
circular references.  See the documentation of the "gc" module for
information on controlling the collection of cyclic garbage. Other
implementations act differently and CPython may change. Do not depend
on immediate finalization of objects when they become unreachable (so
you should always close files explicitly).

Note that the use of the implementation's tracing or debugging
facilities may keep objects alive that would normally be collectable.
Also note that catching an exception with a '"try"..."except"'
statement may keep objects alive.

Some objects contain references to "external" resources such as open
files or windows.  It is understood that these resources are freed
when the object is garbage-collected, but since garbage collection is
not guaranteed to happen, such objects also provide an explicit way to
release the external resource, usually a "close()" method. Programs
are strongly recommended to explicitly close such objects.  The
'"try"..."finally"' statement and the '"with"' statement provide
convenient ways to do this.

Some objects contain references to other objects; these are called
*containers*. Examples of containers are tuples, lists and
dictionaries.  The references are part of a container's value.  In
most cases, when we talk about the value of a container, we imply the
values, not the identities of the contained objects; however, when we
talk about the mutability of a container, only the identities of the
immediately contained objects are implied.  So, if an immutable
container (like a tuple) contains a reference to a mutable object, its
value changes if that mutable object is changed.

Types affect almost all aspects of object behavior.  Even the
importance of object identity is affected in some sense: for immutable
types, operations that compute new values may actually return a
reference to any existing object with the same type and value, while
for mutable objects this is not allowed.  E.g., after "a = 1; b = 1",
"a" and "b" may or may not refer to the same object with the value
one, depending on the implementation, but after "c = []; d = []", "c"
and "d" are guaranteed to refer to two different, unique, newly
created empty lists. (Note that "c = d = []" assigns the same object
to both "c" and "d".)
"""
    , 'operator-summary':
    """Operator precedence
*******************

The following table summarizes the operator precedence in Python, from
lowest precedence (least binding) to highest precedence (most
binding).  Operators in the same box have the same precedence.  Unless
the syntax is explicitly given, operators are binary.  Operators in
the same box group left to right (except for exponentiation, which
groups from right to left).

Note that comparisons, membership tests, and identity tests, all have
the same precedence and have a left-to-right chaining feature as
described in the Comparisons section.

+-------------------------------------------------+---------------------------------------+
| Operator                                        | Description                           |
+=================================================+=======================================+
| "lambda"                                        | Lambda expression                     |
+-------------------------------------------------+---------------------------------------+
| "if" -- "else"                                  | Conditional expression                |
+-------------------------------------------------+---------------------------------------+
| "or"                                            | Boolean OR                            |
+-------------------------------------------------+---------------------------------------+
| "and"                                           | Boolean AND                           |
+-------------------------------------------------+---------------------------------------+
| "not" "x"                                       | Boolean NOT                           |
+-------------------------------------------------+---------------------------------------+
| "in", "not in", "is", "is not", "<", "<=", ">", | Comparisons, including membership     |
| ">=", "!=", "=="                                | tests and identity tests              |
+-------------------------------------------------+---------------------------------------+
| "|"                                             | Bitwise OR                            |
+-------------------------------------------------+---------------------------------------+
| "^"                                             | Bitwise XOR                           |
+-------------------------------------------------+---------------------------------------+
| "&"                                             | Bitwise AND                           |
+-------------------------------------------------+---------------------------------------+
| "<<", ">>"                                      | Shifts                                |
+-------------------------------------------------+---------------------------------------+
| "+", "-"                                        | Addition and subtraction              |
+-------------------------------------------------+---------------------------------------+
| "*", "@", "/", "//", "%"                        | Multiplication, matrix multiplication |
|                                                 | division, remainder [5]               |
+-------------------------------------------------+---------------------------------------+
| "+x", "-x", "~x"                                | Positive, negative, bitwise NOT       |
+-------------------------------------------------+---------------------------------------+
| "**"                                            | Exponentiation [6]                    |
+-------------------------------------------------+---------------------------------------+
| "await" "x"                                     | Await expression                      |
+-------------------------------------------------+---------------------------------------+
| "x[index]", "x[index:index]",                   | Subscription, slicing, call,          |
| "x(arguments...)", "x.attribute"                | attribute reference                   |
+-------------------------------------------------+---------------------------------------+
| "(expressions...)", "[expressions...]", "{key:  | Binding or tuple display, list        |
| value...}", "{expressions...}"                  | display, dictionary display, set      |
|                                                 | display                               |
+-------------------------------------------------+---------------------------------------+

-[ Footnotes ]-

[1] While "abs(x%y) < abs(y)" is true mathematically, for floats
    it may not be true numerically due to roundoff.  For example, and
    assuming a platform on which a Python float is an IEEE 754 double-
    precision number, in order that "-1e-100 % 1e100" have the same
    sign as "1e100", the computed result is "-1e-100 + 1e100", which
    is numerically exactly equal to "1e100".  The function
    "math.fmod()" returns a result whose sign matches the sign of the
    first argument instead, and so returns "-1e-100" in this case.
    Which approach is more appropriate depends on the application.

[2] If x is very close to an exact integer multiple of y, it's
    possible for "x//y" to be one larger than "(x-x%y)//y" due to
    rounding.  In such cases, Python returns the latter result, in
    order to preserve that "divmod(x,y)[0] * y + x % y" be very close
    to "x".

[3] The Unicode standard distinguishes between *code points* (e.g.
    U+0041) and *abstract characters* (e.g. "LATIN CAPITAL LETTER A").
    While most abstract characters in Unicode are only represented
    using one code point, there is a number of abstract characters
    that can in addition be represented using a sequence of more than
    one code point.  For example, the abstract character "LATIN
    CAPITAL LETTER C WITH CEDILLA" can be represented as a single
    *precomposed character* at code position U+00C7, or as a sequence
    of a *base character* at code position U+0043 (LATIN CAPITAL
    LETTER C), followed by a *combining character* at code position
    U+0327 (COMBINING CEDILLA).

    The comparison operators on strings compare at the level of
    Unicode code points. This may be counter-intuitive to humans.  For
    example, ""\\u00C7" == "\\u0043\\u0327"" is "False", even though both
    strings represent the same abstract character "LATIN CAPITAL
    LETTER C WITH CEDILLA".

    To compare strings at the level of abstract characters (that is,
    in a way intuitive to humans), use "unicodedata.normalize()".

[4] Due to automatic garbage-collection, free lists, and the
    dynamic nature of descriptors, you may notice seemingly unusual
    behaviour in certain uses of the "is" operator, like those
    involving comparisons between instance methods, or constants.
    Check their documentation for more info.

[5] The "%" operator is also used for string formatting; the same
    precedence applies.

[6] The power operator "**" binds less tightly than an arithmetic
    or bitwise unary operator on its right, that is, "2**-1" is "0.5".
"""
    , 'pass':
    """The "pass" statement
********************

   pass_stmt ::= "pass"

"pass" is a null operation --- when it is executed, nothing happens.
It is useful as a placeholder when a statement is required
syntactically, but no code needs to be executed, for example:

   def f(arg): pass    # a function that does nothing (yet)

   class C: pass       # a class with no methods (yet)
"""
    , 'power':
    """The power operator
******************

The power operator binds more tightly than unary operators on its
left; it binds less tightly than unary operators on its right.  The
syntax is:

   power ::= ( await_expr | primary ) ["**" u_expr]

Thus, in an unparenthesized sequence of power and unary operators, the
operators are evaluated from right to left (this does not constrain
the evaluation order for the operands): "-1**2" results in "-1".

The power operator has the same semantics as the built-in "pow()"
function, when called with two arguments: it yields its left argument
raised to the power of its right argument.  The numeric arguments are
first converted to a common type, and the result is of that type.

For int operands, the result has the same type as the operands unless
the second argument is negative; in that case, all arguments are
converted to float and a float result is delivered. For example,
"10**2" returns "100", but "10**-2" returns "0.01".

Raising "0.0" to a negative power results in a "ZeroDivisionError".
Raising a negative number to a fractional power results in a "complex"
number. (In earlier versions it raised a "ValueError".)
"""
    , 'raise':
    """The "raise" statement
*********************

   raise_stmt ::= "raise" [expression ["from" expression]]

If no expressions are present, "raise" re-raises the last exception
that was active in the current scope.  If no exception is active in
the current scope, a "RuntimeError" exception is raised indicating
that this is an error.

Otherwise, "raise" evaluates the first expression as the exception
object.  It must be either a subclass or an instance of
"BaseException". If it is a class, the exception instance will be
obtained when needed by instantiating the class with no arguments.

The *type* of the exception is the exception instance's class, the
*value* is the instance itself.

A traceback object is normally created automatically when an exception
is raised and attached to it as the "__traceback__" attribute, which
is writable. You can create an exception and set your own traceback in
one step using the "with_traceback()" exception method (which returns
the same exception instance, with its traceback set to its argument),
like so:

   raise Exception("foo occurred").with_traceback(tracebackobj)

The "from" clause is used for exception chaining: if given, the second
*expression* must be another exception class or instance, which will
then be attached to the raised exception as the "__cause__" attribute
(which is writable).  If the raised exception is not handled, both
exceptions will be printed:

   >>> try:
   ...     print(1 / 0)
   ... except Exception as exc:
   ...     raise RuntimeError("Something bad happened") from exc
   ...
   Traceback (most recent call last):
     File "<stdin>", line 2, in <module>
   ZeroDivisionError: division by zero

   The above exception was the direct cause of the following exception:

   Traceback (most recent call last):
     File "<stdin>", line 4, in <module>
   RuntimeError: Something bad happened

A similar mechanism works implicitly if an exception is raised inside
an exception handler or a "finally" clause: the previous exception is
then attached as the new exception's "__context__" attribute:

   >>> try:
   ...     print(1 / 0)
   ... except:
   ...     raise RuntimeError("Something bad happened")
   ...
   Traceback (most recent call last):
     File "<stdin>", line 2, in <module>
   ZeroDivisionError: division by zero

   During handling of the above exception, another exception occurred:

   Traceback (most recent call last):
     File "<stdin>", line 4, in <module>
   RuntimeError: Something bad happened

Exception chaining can be explicitly suppressed by specifying "None"
in the "from" clause:

   >>> try:
   ...     print(1 / 0)
   ... except:
   ...     raise RuntimeError("Something bad happened") from None
   ...
   Traceback (most recent call last):
     File "<stdin>", line 4, in <module>
   RuntimeError: Something bad happened

Additional information on exceptions can be found in section
Exceptions, and information about handling exceptions is in section
The try statement.

Changed in version 3.3: "None" is now permitted as "Y" in "raise X
from Y".

New in version 3.3: The "__suppress_context__" attribute to suppress
automatic display of the exception context.
"""
    , 'return':
    """The "return" statement
**********************

   return_stmt ::= "return" [expression_list]

"return" may only occur syntactically nested in a function definition,
not within a nested class definition.

If an expression list is present, it is evaluated, else "None" is
substituted.

"return" leaves the current function call with the expression list (or
"None") as return value.

When "return" passes control out of a "try" statement with a "finally"
clause, that "finally" clause is executed before really leaving the
function.

In a generator function, the "return" statement indicates that the
generator is done and will cause "StopIteration" to be raised. The
returned value (if any) is used as an argument to construct
"StopIteration" and becomes the "StopIteration.value" attribute.

In an asynchronous generator function, an empty "return" statement
indicates that the asynchronous generator is done and will cause
"StopAsyncIteration" to be raised.  A non-empty "return" statement is
a syntax error in an asynchronous generator function.
"""
    , 'sequence-types':
    """Emulating container types
*************************

The following methods can be defined to implement container objects.
Containers usually are sequences (such as lists or tuples) or mappings
(like dictionaries), but can represent other containers as well.  The
first set of methods is used either to emulate a sequence or to
emulate a mapping; the difference is that for a sequence, the
allowable keys should be the integers *k* for which "0 <= k < N" where
*N* is the length of the sequence, or slice objects, which define a
range of items.  It is also recommended that mappings provide the
methods "keys()", "values()", "items()", "get()", "clear()",
"setdefault()", "pop()", "popitem()", "copy()", and "update()"
behaving similar to those for Python's standard dictionary objects.
The "collections" module provides a "MutableMapping" abstract base
class to help create those methods from a base set of "__getitem__()",
"__setitem__()", "__delitem__()", and "keys()". Mutable sequences
should provide methods "append()", "count()", "index()", "extend()",
"insert()", "pop()", "remove()", "reverse()" and "sort()", like Python
standard list objects.  Finally, sequence types should implement
addition (meaning concatenation) and multiplication (meaning
repetition) by defining the methods "__add__()", "__radd__()",
"__iadd__()", "__mul__()", "__rmul__()" and "__imul__()" described
below; they should not define other numerical operators.  It is
recommended that both mappings and sequences implement the
"__contains__()" method to allow efficient use of the "in" operator;
for mappings, "in" should search the mapping's keys; for sequences, it
should search through the values.  It is further recommended that both
mappings and sequences implement the "__iter__()" method to allow
efficient iteration through the container; for mappings, "__iter__()"
should be the same as "keys()"; for sequences, it should iterate
through the values.

object.__len__(self)

   Called to implement the built-in function "len()".  Should return
   the length of the object, an integer ">=" 0.  Also, an object that
   doesn't define a "__bool__()" method and whose "__len__()" method
   returns zero is considered to be false in a Boolean context.

   **CPython implementation detail:** In CPython, the length is
   required to be at most "sys.maxsize". If the length is larger than
   "sys.maxsize" some features (such as "len()") may raise
   "OverflowError".  To prevent raising "OverflowError" by truth value
   testing, an object must define a "__bool__()" method.

object.__length_hint__(self)

   Called to implement "operator.length_hint()". Should return an
   estimated length for the object (which may be greater or less than
   the actual length). The length must be an integer ">=" 0. This
   method is purely an optimization and is never required for
   correctness.

   New in version 3.4.

Note: Slicing is done exclusively with the following three methods.
  A call like

     a[1:2] = b

  is translated to

     a[slice(1, 2, None)] = b

  and so forth.  Missing slice items are always filled in with "None".

object.__getitem__(self, key)

   Called to implement evaluation of "self[key]". For sequence types,
   the accepted keys should be integers and slice objects.  Note that
   the special interpretation of negative indexes (if the class wishes
   to emulate a sequence type) is up to the "__getitem__()" method. If
   *key* is of an inappropriate type, "TypeError" may be raised; if of
   a value outside the set of indexes for the sequence (after any
   special interpretation of negative values), "IndexError" should be
   raised. For mapping types, if *key* is missing (not in the
   container), "KeyError" should be raised.

   Note: "for" loops expect that an "IndexError" will be raised for
     illegal indexes to allow proper detection of the end of the
     sequence.

object.__missing__(self, key)

   Called by "dict"."__getitem__()" to implement "self[key]" for dict
   subclasses when key is not in the dictionary.

object.__setitem__(self, key, value)

   Called to implement assignment to "self[key]".  Same note as for
   "__getitem__()".  This should only be implemented for mappings if
   the objects support changes to the values for keys, or if new keys
   can be added, or for sequences if elements can be replaced.  The
   same exceptions should be raised for improper *key* values as for
   the "__getitem__()" method.

object.__delitem__(self, key)

   Called to implement deletion of "self[key]".  Same note as for
   "__getitem__()".  This should only be implemented for mappings if
   the objects support removal of keys, or for sequences if elements
   can be removed from the sequence.  The same exceptions should be
   raised for improper *key* values as for the "__getitem__()" method.

object.__iter__(self)

   This method is called when an iterator is required for a container.
   This method should return a new iterator object that can iterate
   over all the objects in the container.  For mappings, it should
   iterate over the keys of the container.

   Iterator objects also need to implement this method; they are
   required to return themselves.  For more information on iterator
   objects, see Iterator Types.

object.__reversed__(self)

   Called (if present) by the "reversed()" built-in to implement
   reverse iteration.  It should return a new iterator object that
   iterates over all the objects in the container in reverse order.

   If the "__reversed__()" method is not provided, the "reversed()"
   built-in will fall back to using the sequence protocol ("__len__()"
   and "__getitem__()").  Objects that support the sequence protocol
   should only provide "__reversed__()" if they can provide an
   implementation that is more efficient than the one provided by
   "reversed()".

The membership test operators ("in" and "not in") are normally
implemented as an iteration through a sequence.  However, container
objects can supply the following special method with a more efficient
implementation, which also does not require the object be a sequence.

object.__contains__(self, item)

   Called to implement membership test operators.  Should return true
   if *item* is in *self*, false otherwise.  For mapping objects, this
   should consider the keys of the mapping rather than the values or
   the key-item pairs.

   For objects that don't define "__contains__()", the membership test
   first tries iteration via "__iter__()", then the old sequence
   iteration protocol via "__getitem__()", see this section in the
   language reference.
"""
    , 'shifting':
    """Shifting operations
*******************

The shifting operations have lower priority than the arithmetic
operations:

   shift_expr ::= a_expr | shift_expr ( "<<" | ">>" ) a_expr

These operators accept integers as arguments.  They shift the first
argument to the left or right by the number of bits given by the
second argument.

A right shift by *n* bits is defined as floor division by "pow(2,n)".
A left shift by *n* bits is defined as multiplication with "pow(2,n)".

Note: In the current implementation, the right-hand operand is
  required to be at most "sys.maxsize".  If the right-hand operand is
  larger than "sys.maxsize" an "OverflowError" exception is raised.
"""
    , 'slicings':
    """Slicings
********

A slicing selects a range of items in a sequence object (e.g., a
string, tuple or list).  Slicings may be used as expressions or as
targets in assignment or "del" statements.  The syntax for a slicing:

   slicing      ::= primary "[" slice_list "]"
   slice_list   ::= slice_item ("," slice_item)* [","]
   slice_item   ::= expression | proper_slice
   proper_slice ::= [lower_bound] ":" [upper_bound] [ ":" [stride] ]
   lower_bound  ::= expression
   upper_bound  ::= expression
   stride       ::= expression

There is ambiguity in the formal syntax here: anything that looks like
an expression list also looks like a slice list, so any subscription
can be interpreted as a slicing.  Rather than further complicating the
syntax, this is disambiguated by defining that in this case the
interpretation as a subscription takes priority over the
interpretation as a slicing (this is the case if the slice list
contains no proper slice).

The semantics for a slicing are as follows.  The primary is indexed
(using the same "__getitem__()" method as normal subscription) with a
key that is constructed from the slice list, as follows.  If the slice
list contains at least one comma, the key is a tuple containing the
conversion of the slice items; otherwise, the conversion of the lone
slice item is the key.  The conversion of a slice item that is an
expression is that expression.  The conversion of a proper slice is a
slice object (see section The standard type hierarchy) whose "start",
"stop" and "step" attributes are the values of the expressions given
as lower bound, upper bound and stride, respectively, substituting
"None" for missing expressions.
"""
    , 'specialattrs':
    """Special Attributes
******************

The implementation adds a few special read-only attributes to several
object types, where they are relevant.  Some of these are not reported
by the "dir()" built-in function.

object.__dict__

   A dictionary or other mapping object used to store an object's
   (writable) attributes.

instance.__class__

   The class to which a class instance belongs.

class.__bases__

   The tuple of base classes of a class object.

definition.__name__

   The name of the class, function, method, descriptor, or generator
   instance.

definition.__qualname__

   The *qualified name* of the class, function, method, descriptor, or
   generator instance.

   New in version 3.3.

class.__mro__

   This attribute is a tuple of classes that are considered when
   looking for base classes during method resolution.

class.mro()

   This method can be overridden by a metaclass to customize the
   method resolution order for its instances.  It is called at class
   instantiation, and its result is stored in "__mro__".

class.__subclasses__()

   Each class keeps a list of weak references to its immediate
   subclasses.  This method returns a list of all those references
   still alive. Example:

      >>> int.__subclasses__()
      [<class 'bool'>]

-[ Footnotes ]-

[1] Additional information on these special methods may be found
    in the Python Reference Manual (Basic customization).

[2] As a consequence, the list "[1, 2]" is considered equal to
    "[1.0, 2.0]", and similarly for tuples.

[3] They must have since the parser can't tell the type of the
    operands.

[4] Cased characters are those with general category property
    being one of "Lu" (Letter, uppercase), "Ll" (Letter, lowercase),
    or "Lt" (Letter, titlecase).

[5] To format only a tuple you should therefore provide a
    singleton tuple whose only element is the tuple to be formatted.
"""
    , 'specialnames':
    """Special method names
********************

A class can implement certain operations that are invoked by special
syntax (such as arithmetic operations or subscripting and slicing) by
defining methods with special names. This is Python's approach to
*operator overloading*, allowing classes to define their own behavior
with respect to language operators.  For instance, if a class defines
a method named "__getitem__()", and "x" is an instance of this class,
then "x[i]" is roughly equivalent to "type(x).__getitem__(x, i)".
Except where mentioned, attempts to execute an operation raise an
exception when no appropriate method is defined (typically
"AttributeError" or "TypeError").

Setting a special method to "None" indicates that the corresponding
operation is not available.  For example, if a class sets "__iter__()"
to "None", the class is not iterable, so calling "iter()" on its
instances will raise a "TypeError" (without falling back to
"__getitem__()"). [2]

When implementing a class that emulates any built-in type, it is
important that the emulation only be implemented to the degree that it
makes sense for the object being modelled.  For example, some
sequences may work well with retrieval of individual elements, but
extracting a slice may not make sense.  (One example of this is the
"NodeList" interface in the W3C's Document Object Model.)


Basic customization
===================

object.__new__(cls[, ...])

   Called to create a new instance of class *cls*.  "__new__()" is a
   static method (special-cased so you need not declare it as such)
   that takes the class of which an instance was requested as its
   first argument.  The remaining arguments are those passed to the
   object constructor expression (the call to the class).  The return
   value of "__new__()" should be the new object instance (usually an
   instance of *cls*).

   Typical implementations create a new instance of the class by
   invoking the superclass's "__new__()" method using
   "super().__new__(cls[, ...])" with appropriate arguments and then
   modifying the newly-created instance as necessary before returning
   it.

   If "__new__()" returns an instance of *cls*, then the new
   instance's "__init__()" method will be invoked like
   "__init__(self[, ...])", where *self* is the new instance and the
   remaining arguments are the same as were passed to "__new__()".

   If "__new__()" does not return an instance of *cls*, then the new
   instance's "__init__()" method will not be invoked.

   "__new__()" is intended mainly to allow subclasses of immutable
   types (like int, str, or tuple) to customize instance creation.  It
   is also commonly overridden in custom metaclasses in order to
   customize class creation.

object.__init__(self[, ...])

   Called after the instance has been created (by "__new__()"), but
   before it is returned to the caller.  The arguments are those
   passed to the class constructor expression.  If a base class has an
   "__init__()" method, the derived class's "__init__()" method, if
   any, must explicitly call it to ensure proper initialization of the
   base class part of the instance; for example:
   "super().__init__([args...])".

   Because "__new__()" and "__init__()" work together in constructing
   objects ("__new__()" to create it, and "__init__()" to customize
   it), no non-"None" value may be returned by "__init__()"; doing so
   will cause a "TypeError" to be raised at runtime.

object.__del__(self)

   Called when the instance is about to be destroyed.  This is also
   called a destructor.  If a base class has a "__del__()" method, the
   derived class's "__del__()" method, if any, must explicitly call it
   to ensure proper deletion of the base class part of the instance.
   Note that it is possible (though not recommended!) for the
   "__del__()" method to postpone destruction of the instance by
   creating a new reference to it.  It may then be called at a later
   time when this new reference is deleted.  It is not guaranteed that
   "__del__()" methods are called for objects that still exist when
   the interpreter exits.

   Note: "del x" doesn't directly call "x.__del__()" --- the former
     decrements the reference count for "x" by one, and the latter is
     only called when "x"'s reference count reaches zero.  Some common
     situations that may prevent the reference count of an object from
     going to zero include: circular references between objects (e.g.,
     a doubly-linked list or a tree data structure with parent and
     child pointers); a reference to the object on the stack frame of
     a function that caught an exception (the traceback stored in
     "sys.exc_info()[2]" keeps the stack frame alive); or a reference
     to the object on the stack frame that raised an unhandled
     exception in interactive mode (the traceback stored in
     "sys.last_traceback" keeps the stack frame alive).  The first
     situation can only be remedied by explicitly breaking the cycles;
     the second can be resolved by freeing the reference to the
     traceback object when it is no longer useful, and the third can
     be resolved by storing "None" in "sys.last_traceback". Circular
     references which are garbage are detected and cleaned up when the
     cyclic garbage collector is enabled (it's on by default). Refer
     to the documentation for the "gc" module for more information
     about this topic.

   Warning: Due to the precarious circumstances under which
     "__del__()" methods are invoked, exceptions that occur during
     their execution are ignored, and a warning is printed to
     "sys.stderr" instead. Also, when "__del__()" is invoked in
     response to a module being deleted (e.g., when execution of the
     program is done), other globals referenced by the "__del__()"
     method may already have been deleted or in the process of being
     torn down (e.g. the import machinery shutting down).  For this
     reason, "__del__()" methods should do the absolute minimum needed
     to maintain external invariants.  Starting with version 1.5,
     Python guarantees that globals whose name begins with a single
     underscore are deleted from their module before other globals are
     deleted; if no other references to such globals exist, this may
     help in assuring that imported modules are still available at the
     time when the "__del__()" method is called.

object.__repr__(self)

   Called by the "repr()" built-in function to compute the "official"
   string representation of an object.  If at all possible, this
   should look like a valid Python expression that could be used to
   recreate an object with the same value (given an appropriate
   environment).  If this is not possible, a string of the form
   "<...some useful description...>" should be returned. The return
   value must be a string object. If a class defines "__repr__()" but
   not "__str__()", then "__repr__()" is also used when an "informal"
   string representation of instances of that class is required.

   This is typically used for debugging, so it is important that the
   representation is information-rich and unambiguous.

object.__str__(self)

   Called by "str(object)" and the built-in functions "format()" and
   "print()" to compute the "informal" or nicely printable string
   representation of an object.  The return value must be a string
   object.

   This method differs from "object.__repr__()" in that there is no
   expectation that "__str__()" return a valid Python expression: a
   more convenient or concise representation can be used.

   The default implementation defined by the built-in type "object"
   calls "object.__repr__()".

object.__bytes__(self)

   Called by bytes to compute a byte-string representation of an
   object. This should return a "bytes" object.

object.__format__(self, format_spec)

   Called by the "format()" built-in function, and by extension,
   evaluation of formatted string literals and the "str.format()"
   method, to produce a "formatted" string representation of an
   object. The "format_spec" argument is a string that contains a
   description of the formatting options desired. The interpretation
   of the "format_spec" argument is up to the type implementing
   "__format__()", however most classes will either delegate
   formatting to one of the built-in types, or use a similar
   formatting option syntax.

   See Format Specification Mini-Language for a description of the
   standard formatting syntax.

   The return value must be a string object.

   Changed in version 3.4: The __format__ method of "object" itself
   raises a "TypeError" if passed any non-empty string.

object.__lt__(self, other)
object.__le__(self, other)
object.__eq__(self, other)
object.__ne__(self, other)
object.__gt__(self, other)
object.__ge__(self, other)

   These are the so-called "rich comparison" methods. The
   correspondence between operator symbols and method names is as
   follows: "x<y" calls "x.__lt__(y)", "x<=y" calls "x.__le__(y)",
   "x==y" calls "x.__eq__(y)", "x!=y" calls "x.__ne__(y)", "x>y" calls
   "x.__gt__(y)", and "x>=y" calls "x.__ge__(y)".

   A rich comparison method may return the singleton "NotImplemented"
   if it does not implement the operation for a given pair of
   arguments. By convention, "False" and "True" are returned for a
   successful comparison. However, these methods can return any value,
   so if the comparison operator is used in a Boolean context (e.g.,
   in the condition of an "if" statement), Python will call "bool()"
   on the value to determine if the result is true or false.

   By default, "__ne__()" delegates to "__eq__()" and inverts the
   result unless it is "NotImplemented".  There are no other implied
   relationships among the comparison operators, for example, the
   truth of "(x<y or x==y)" does not imply "x<=y". To automatically
   generate ordering operations from a single root operation, see
   "functools.total_ordering()".

   See the paragraph on "__hash__()" for some important notes on
   creating *hashable* objects which support custom comparison
   operations and are usable as dictionary keys.

   There are no swapped-argument versions of these methods (to be used
   when the left argument does not support the operation but the right
   argument does); rather, "__lt__()" and "__gt__()" are each other's
   reflection, "__le__()" and "__ge__()" are each other's reflection,
   and "__eq__()" and "__ne__()" are their own reflection. If the
   operands are of different types, and right operand's type is a
   direct or indirect subclass of the left operand's type, the
   reflected method of the right operand has priority, otherwise the
   left operand's method has priority.  Virtual subclassing is not
   considered.

object.__hash__(self)

   Called by built-in function "hash()" and for operations on members
   of hashed collections including "set", "frozenset", and "dict".
   "__hash__()" should return an integer. The only required property
   is that objects which compare equal have the same hash value; it is
   advised to mix together the hash values of the components of the
   object that also play a part in comparison of objects by packing
   them into a tuple and hashing the tuple. Example:

      def __hash__(self):
          return hash((self.name, self.nick, self.color))

   Note: "hash()" truncates the value returned from an object's
     custom "__hash__()" method to the size of a "Py_ssize_t".  This
     is typically 8 bytes on 64-bit builds and 4 bytes on 32-bit
     builds. If an object's   "__hash__()" must interoperate on builds
     of different bit sizes, be sure to check the width on all
     supported builds.  An easy way to do this is with "python -c
     "import sys; print(sys.hash_info.width)"".

   If a class does not define an "__eq__()" method it should not
   define a "__hash__()" operation either; if it defines "__eq__()"
   but not "__hash__()", its instances will not be usable as items in
   hashable collections.  If a class defines mutable objects and
   implements an "__eq__()" method, it should not implement
   "__hash__()", since the implementation of hashable collections
   requires that a key's hash value is immutable (if the object's hash
   value changes, it will be in the wrong hash bucket).

   User-defined classes have "__eq__()" and "__hash__()" methods by
   default; with them, all objects compare unequal (except with
   themselves) and "x.__hash__()" returns an appropriate value such
   that "x == y" implies both that "x is y" and "hash(x) == hash(y)".

   A class that overrides "__eq__()" and does not define "__hash__()"
   will have its "__hash__()" implicitly set to "None".  When the
   "__hash__()" method of a class is "None", instances of the class
   will raise an appropriate "TypeError" when a program attempts to
   retrieve their hash value, and will also be correctly identified as
   unhashable when checking "isinstance(obj, collections.Hashable)".

   If a class that overrides "__eq__()" needs to retain the
   implementation of "__hash__()" from a parent class, the interpreter
   must be told this explicitly by setting "__hash__ =
   <ParentClass>.__hash__".

   If a class that does not override "__eq__()" wishes to suppress
   hash support, it should include "__hash__ = None" in the class
   definition. A class which defines its own "__hash__()" that
   explicitly raises a "TypeError" would be incorrectly identified as
   hashable by an "isinstance(obj, collections.Hashable)" call.

   Note: By default, the "__hash__()" values of str, bytes and
     datetime objects are "salted" with an unpredictable random value.
     Although they remain constant within an individual Python
     process, they are not predictable between repeated invocations of
     Python.This is intended to provide protection against a denial-
     of-service caused by carefully-chosen inputs that exploit the
     worst case performance of a dict insertion, O(n^2) complexity.
     See http://www.ocert.org/advisories/ocert-2011-003.html for
     details.Changing hash values affects the iteration order of
     dicts, sets and other mappings.  Python has never made guarantees
     about this ordering (and it typically varies between 32-bit and
     64-bit builds).See also "PYTHONHASHSEED".

   Changed in version 3.3: Hash randomization is enabled by default.

object.__bool__(self)

   Called to implement truth value testing and the built-in operation
   "bool()"; should return "False" or "True".  When this method is not
   defined, "__len__()" is called, if it is defined, and the object is
   considered true if its result is nonzero.  If a class defines
   neither "__len__()" nor "__bool__()", all its instances are
   considered true.


Customizing attribute access
============================

The following methods can be defined to customize the meaning of
attribute access (use of, assignment to, or deletion of "x.name") for
class instances.

object.__getattr__(self, name)

   Called when an attribute lookup has not found the attribute in the
   usual places (i.e. it is not an instance attribute nor is it found
   in the class tree for "self").  "name" is the attribute name. This
   method should return the (computed) attribute value or raise an
   "AttributeError" exception.

   Note that if the attribute is found through the normal mechanism,
   "__getattr__()" is not called.  (This is an intentional asymmetry
   between "__getattr__()" and "__setattr__()".) This is done both for
   efficiency reasons and because otherwise "__getattr__()" would have
   no way to access other attributes of the instance.  Note that at
   least for instance variables, you can fake total control by not
   inserting any values in the instance attribute dictionary (but
   instead inserting them in another object).  See the
   "__getattribute__()" method below for a way to actually get total
   control over attribute access.

object.__getattribute__(self, name)

   Called unconditionally to implement attribute accesses for
   instances of the class. If the class also defines "__getattr__()",
   the latter will not be called unless "__getattribute__()" either
   calls it explicitly or raises an "AttributeError". This method
   should return the (computed) attribute value or raise an
   "AttributeError" exception. In order to avoid infinite recursion in
   this method, its implementation should always call the base class
   method with the same name to access any attributes it needs, for
   example, "object.__getattribute__(self, name)".

   Note: This method may still be bypassed when looking up special
     methods as the result of implicit invocation via language syntax
     or built-in functions. See Special method lookup.

object.__setattr__(self, name, value)

   Called when an attribute assignment is attempted.  This is called
   instead of the normal mechanism (i.e. store the value in the
   instance dictionary). *name* is the attribute name, *value* is the
   value to be assigned to it.

   If "__setattr__()" wants to assign to an instance attribute, it
   should call the base class method with the same name, for example,
   "object.__setattr__(self, name, value)".

object.__delattr__(self, name)

   Like "__setattr__()" but for attribute deletion instead of
   assignment.  This should only be implemented if "del obj.name" is
   meaningful for the object.

object.__dir__(self)

   Called when "dir()" is called on the object. A sequence must be
   returned. "dir()" converts the returned sequence to a list and
   sorts it.


Implementing Descriptors
------------------------

The following methods only apply when an instance of the class
containing the method (a so-called *descriptor* class) appears in an
*owner* class (the descriptor must be in either the owner's class
dictionary or in the class dictionary for one of its parents).  In the
examples below, "the attribute" refers to the attribute whose name is
the key of the property in the owner class' "__dict__".

object.__get__(self, instance, owner)

   Called to get the attribute of the owner class (class attribute
   access) or of an instance of that class (instance attribute
   access). *owner* is always the owner class, while *instance* is the
   instance that the attribute was accessed through, or "None" when
   the attribute is accessed through the *owner*.  This method should
   return the (computed) attribute value or raise an "AttributeError"
   exception.

object.__set__(self, instance, value)

   Called to set the attribute on an instance *instance* of the owner
   class to a new value, *value*.

object.__delete__(self, instance)

   Called to delete the attribute on an instance *instance* of the
   owner class.

object.__set_name__(self, owner, name)

   Called at the time the owning class *owner* is created. The
   descriptor has been assigned to *name*.

   New in version 3.6.

The attribute "__objclass__" is interpreted by the "inspect" module as
specifying the class where this object was defined (setting this
appropriately can assist in runtime introspection of dynamic class
attributes). For callables, it may indicate that an instance of the
given type (or a subclass) is expected or required as the first
positional argument (for example, CPython sets this attribute for
unbound methods that are implemented in C).


Invoking Descriptors
--------------------

In general, a descriptor is an object attribute with "binding
behavior", one whose attribute access has been overridden by methods
in the descriptor protocol:  "__get__()", "__set__()", and
"__delete__()". If any of those methods are defined for an object, it
is said to be a descriptor.

The default behavior for attribute access is to get, set, or delete
the attribute from an object's dictionary. For instance, "a.x" has a
lookup chain starting with "a.__dict__['x']", then
"type(a).__dict__['x']", and continuing through the base classes of
"type(a)" excluding metaclasses.

However, if the looked-up value is an object defining one of the
descriptor methods, then Python may override the default behavior and
invoke the descriptor method instead.  Where this occurs in the
precedence chain depends on which descriptor methods were defined and
how they were called.

The starting point for descriptor invocation is a binding, "a.x". How
the arguments are assembled depends on "a":

Direct Call
   The simplest and least common call is when user code directly
   invokes a descriptor method:    "x.__get__(a)".

Instance Binding
   If binding to an object instance, "a.x" is transformed into the
   call: "type(a).__dict__['x'].__get__(a, type(a))".

Class Binding
   If binding to a class, "A.x" is transformed into the call:
   "A.__dict__['x'].__get__(None, A)".

Super Binding
   If "a" is an instance of "super", then the binding "super(B,
   obj).m()" searches "obj.__class__.__mro__" for the base class "A"
   immediately preceding "B" and then invokes the descriptor with the
   call: "A.__dict__['m'].__get__(obj, obj.__class__)".

For instance bindings, the precedence of descriptor invocation depends
on the which descriptor methods are defined.  A descriptor can define
any combination of "__get__()", "__set__()" and "__delete__()".  If it
does not define "__get__()", then accessing the attribute will return
the descriptor object itself unless there is a value in the object's
instance dictionary.  If the descriptor defines "__set__()" and/or
"__delete__()", it is a data descriptor; if it defines neither, it is
a non-data descriptor.  Normally, data descriptors define both
"__get__()" and "__set__()", while non-data descriptors have just the
"__get__()" method.  Data descriptors with "__set__()" and "__get__()"
defined always override a redefinition in an instance dictionary.  In
contrast, non-data descriptors can be overridden by instances.

Python methods (including "staticmethod()" and "classmethod()") are
implemented as non-data descriptors.  Accordingly, instances can
redefine and override methods.  This allows individual instances to
acquire behaviors that differ from other instances of the same class.

The "property()" function is implemented as a data descriptor.
Accordingly, instances cannot override the behavior of a property.


__slots__
---------

By default, instances of classes have a dictionary for attribute
storage.  This wastes space for objects having very few instance
variables.  The space consumption can become acute when creating large
numbers of instances.

The default can be overridden by defining *__slots__* in a class
definition. The *__slots__* declaration takes a sequence of instance
variables and reserves just enough space in each instance to hold a
value for each variable.  Space is saved because *__dict__* is not
created for each instance.

object.__slots__

   This class variable can be assigned a string, iterable, or sequence
   of strings with variable names used by instances.  *__slots__*
   reserves space for the declared variables and prevents the
   automatic creation of *__dict__* and *__weakref__* for each
   instance.


Notes on using *__slots__*
~~~~~~~~~~~~~~~~~~~~~~~~~~

* When inheriting from a class without *__slots__*, the *__dict__*
  attribute of that class will always be accessible, so a *__slots__*
  definition in the subclass is meaningless.

* Without a *__dict__* variable, instances cannot be assigned new
  variables not listed in the *__slots__* definition.  Attempts to
  assign to an unlisted variable name raises "AttributeError". If
  dynamic assignment of new variables is desired, then add
  "'__dict__'" to the sequence of strings in the *__slots__*
  declaration.

* Without a *__weakref__* variable for each instance, classes
  defining *__slots__* do not support weak references to its
  instances. If weak reference support is needed, then add
  "'__weakref__'" to the sequence of strings in the *__slots__*
  declaration.

* *__slots__* are implemented at the class level by creating
  descriptors (Implementing Descriptors) for each variable name.  As a
  result, class attributes cannot be used to set default values for
  instance variables defined by *__slots__*; otherwise, the class
  attribute would overwrite the descriptor assignment.

* The action of a *__slots__* declaration is limited to the class
  where it is defined.  As a result, subclasses will have a *__dict__*
  unless they also define *__slots__* (which must only contain names
  of any *additional* slots).

* If a class defines a slot also defined in a base class, the
  instance variable defined by the base class slot is inaccessible
  (except by retrieving its descriptor directly from the base class).
  This renders the meaning of the program undefined.  In the future, a
  check may be added to prevent this.

* Nonempty *__slots__* does not work for classes derived from
  "variable-length" built-in types such as "int", "bytes" and "tuple".

* Any non-string iterable may be assigned to *__slots__*. Mappings
  may also be used; however, in the future, special meaning may be
  assigned to the values corresponding to each key.

* *__class__* assignment works only if both classes have the same
  *__slots__*.


Customizing class creation
==========================

Whenever a class inherits from another class, *__init_subclass__* is
called on that class. This way, it is possible to write classes which
change the behavior of subclasses. This is closely related to class
decorators, but where class decorators only affect the specific class
they're applied to, "__init_subclass__" solely applies to future
subclasses of the class defining the method.

classmethod object.__init_subclass__(cls)

   This method is called whenever the containing class is subclassed.
   *cls* is then the new subclass. If defined as a normal instance
   method, this method is implicitly converted to a class method.

   Keyword arguments which are given to a new class are passed to the
   parent's class "__init_subclass__". For compatibility with other
   classes using "__init_subclass__", one should take out the needed
   keyword arguments and pass the others over to the base class, as
   in:

      class Philosopher:
          def __init_subclass__(cls, default_name, **kwargs):
              super().__init_subclass__(**kwargs)
              cls.default_name = default_name

      class AustralianPhilosopher(Philosopher, default_name="Bruce"):
          pass

   The default implementation "object.__init_subclass__" does nothing,
   but raises an error if it is called with any arguments.

   Note: The metaclass hint "metaclass" is consumed by the rest of
     the type machinery, and is never passed to "__init_subclass__"
     implementations. The actual metaclass (rather than the explicit
     hint) can be accessed as "type(cls)".

   New in version 3.6.


Metaclasses
-----------

By default, classes are constructed using "type()". The class body is
executed in a new namespace and the class name is bound locally to the
result of "type(name, bases, namespace)".

The class creation process can be customized by passing the
"metaclass" keyword argument in the class definition line, or by
inheriting from an existing class that included such an argument. In
the following example, both "MyClass" and "MySubclass" are instances
of "Meta":

   class Meta(type):
       pass

   class MyClass(metaclass=Meta):
       pass

   class MySubclass(MyClass):
       pass

Any other keyword arguments that are specified in the class definition
are passed through to all metaclass operations described below.

When a class definition is executed, the following steps occur:

* the appropriate metaclass is determined

* the class namespace is prepared

* the class body is executed

* the class object is created


Determining the appropriate metaclass
-------------------------------------

The appropriate metaclass for a class definition is determined as
follows:

* if no bases and no explicit metaclass are given, then "type()" is
  used

* if an explicit metaclass is given and it is *not* an instance of
  "type()", then it is used directly as the metaclass

* if an instance of "type()" is given as the explicit metaclass, or
  bases are defined, then the most derived metaclass is used

The most derived metaclass is selected from the explicitly specified
metaclass (if any) and the metaclasses (i.e. "type(cls)") of all
specified base classes. The most derived metaclass is one which is a
subtype of *all* of these candidate metaclasses. If none of the
candidate metaclasses meets that criterion, then the class definition
will fail with "TypeError".


Preparing the class namespace
-----------------------------

Once the appropriate metaclass has been identified, then the class
namespace is prepared. If the metaclass has a "__prepare__" attribute,
it is called as "namespace = metaclass.__prepare__(name, bases,
**kwds)" (where the additional keyword arguments, if any, come from
the class definition).

If the metaclass has no "__prepare__" attribute, then the class
namespace is initialised as an empty ordered mapping.

See also:

  **PEP 3115** - Metaclasses in Python 3000
     Introduced the "__prepare__" namespace hook


Executing the class body
------------------------

The class body is executed (approximately) as "exec(body, globals(),
namespace)". The key difference from a normal call to "exec()" is that
lexical scoping allows the class body (including any methods) to
reference names from the current and outer scopes when the class
definition occurs inside a function.

However, even when the class definition occurs inside the function,
methods defined inside the class still cannot see names defined at the
class scope. Class variables must be accessed through the first
parameter of instance or class methods, or through the implicit
lexically scoped "__class__" reference described in the next section.


Creating the class object
-------------------------

Once the class namespace has been populated by executing the class
body, the class object is created by calling "metaclass(name, bases,
namespace, **kwds)" (the additional keywords passed here are the same
as those passed to "__prepare__").

This class object is the one that will be referenced by the zero-
argument form of "super()". "__class__" is an implicit closure
reference created by the compiler if any methods in a class body refer
to either "__class__" or "super". This allows the zero argument form
of "super()" to correctly identify the class being defined based on
lexical scoping, while the class or instance that was used to make the
current call is identified based on the first argument passed to the
method.

**CPython implementation detail:** In CPython 3.6 and later, the
"__class__" cell is passed to the metaclass as a "__classcell__" entry
in the class namespace. If present, this must be propagated up to the
"type.__new__" call in order for the class to be initialised
correctly. Failing to do so will result in a "DeprecationWarning" in
Python 3.6, and a "RuntimeWarning" in the future.

When using the default metaclass "type", or any metaclass that
ultimately calls "type.__new__", the following additional
customisation steps are invoked after creating the class object:

* first, "type.__new__" collects all of the descriptors in the class
  namespace that define a "__set_name__()" method;

* second, all of these "__set_name__" methods are called with the
  class being defined and the assigned name of that particular
  descriptor; and

* finally, the "__init_subclass__()" hook is called on the immediate
  parent of the new class in its method resolution order.

After the class object is created, it is passed to the class
decorators included in the class definition (if any) and the resulting
object is bound in the local namespace as the defined class.

When a new class is created by "type.__new__", the object provided as
the namespace parameter is copied to a new ordered mapping and the
original object is discarded. The new copy is wrapped in a read-only
proxy, which becomes the "__dict__" attribute of the class object.

See also:

  **PEP 3135** - New super
     Describes the implicit "__class__" closure reference


Metaclass example
-----------------

The potential uses for metaclasses are boundless. Some ideas that have
been explored include logging, interface checking, automatic
delegation, automatic property creation, proxies, frameworks, and
automatic resource locking/synchronization.

Here is an example of a metaclass that uses an
"collections.OrderedDict" to remember the order that class variables
are defined:

   class OrderedClass(type):

       @classmethod
       def __prepare__(metacls, name, bases, **kwds):
           return collections.OrderedDict()

       def __new__(cls, name, bases, namespace, **kwds):
           result = type.__new__(cls, name, bases, dict(namespace))
           result.members = tuple(namespace)
           return result

   class A(metaclass=OrderedClass):
       def one(self): pass
       def two(self): pass
       def three(self): pass
       def four(self): pass

   >>> A.members
   ('__module__', 'one', 'two', 'three', 'four')

When the class definition for *A* gets executed, the process begins
with calling the metaclass's "__prepare__()" method which returns an
empty "collections.OrderedDict".  That mapping records the methods and
attributes of *A* as they are defined within the body of the class
statement. Once those definitions are executed, the ordered dictionary
is fully populated and the metaclass's "__new__()" method gets
invoked.  That method builds the new type and it saves the ordered
dictionary keys in an attribute called "members".


Customizing instance and subclass checks
========================================

The following methods are used to override the default behavior of the
"isinstance()" and "issubclass()" built-in functions.

In particular, the metaclass "abc.ABCMeta" implements these methods in
order to allow the addition of Abstract Base Classes (ABCs) as
"virtual base classes" to any class or type (including built-in
types), including other ABCs.

class.__instancecheck__(self, instance)

   Return true if *instance* should be considered a (direct or
   indirect) instance of *class*. If defined, called to implement
   "isinstance(instance, class)".

class.__subclasscheck__(self, subclass)

   Return true if *subclass* should be considered a (direct or
   indirect) subclass of *class*.  If defined, called to implement
   "issubclass(subclass, class)".

Note that these methods are looked up on the type (metaclass) of a
class.  They cannot be defined as class methods in the actual class.
This is consistent with the lookup of special methods that are called
on instances, only in this case the instance is itself a class.

See also:

  **PEP 3119** - Introducing Abstract Base Classes
     Includes the specification for customizing "isinstance()" and
     "issubclass()" behavior through "__instancecheck__()" and
     "__subclasscheck__()", with motivation for this functionality in
     the context of adding Abstract Base Classes (see the "abc"
     module) to the language.


Emulating callable objects
==========================

object.__call__(self[, args...])

   Called when the instance is "called" as a function; if this method
   is defined, "x(arg1, arg2, ...)" is a shorthand for
   "x.__call__(arg1, arg2, ...)".


Emulating container types
=========================

The following methods can be defined to implement container objects.
Containers usually are sequences (such as lists or tuples) or mappings
(like dictionaries), but can represent other containers as well.  The
first set of methods is used either to emulate a sequence or to
emulate a mapping; the difference is that for a sequence, the
allowable keys should be the integers *k* for which "0 <= k < N" where
*N* is the length of the sequence, or slice objects, which define a
range of items.  It is also recommended that mappings provide the
methods "keys()", "values()", "items()", "get()", "clear()",
"setdefault()", "pop()", "popitem()", "copy()", and "update()"
behaving similar to those for Python's standard dictionary objects.
The "collections" module provides a "MutableMapping" abstract base
class to help create those methods from a base set of "__getitem__()",
"__setitem__()", "__delitem__()", and "keys()". Mutable sequences
should provide methods "append()", "count()", "index()", "extend()",
"insert()", "pop()", "remove()", "reverse()" and "sort()", like Python
standard list objects.  Finally, sequence types should implement
addition (meaning concatenation) and multiplication (meaning
repetition) by defining the methods "__add__()", "__radd__()",
"__iadd__()", "__mul__()", "__rmul__()" and "__imul__()" described
below; they should not define other numerical operators.  It is
recommended that both mappings and sequences implement the
"__contains__()" method to allow efficient use of the "in" operator;
for mappings, "in" should search the mapping's keys; for sequences, it
should search through the values.  It is further recommended that both
mappings and sequences implement the "__iter__()" method to allow
efficient iteration through the container; for mappings, "__iter__()"
should be the same as "keys()"; for sequences, it should iterate
through the values.

object.__len__(self)

   Called to implement the built-in function "len()".  Should return
   the length of the object, an integer ">=" 0.  Also, an object that
   doesn't define a "__bool__()" method and whose "__len__()" method
   returns zero is considered to be false in a Boolean context.

   **CPython implementation detail:** In CPython, the length is
   required to be at most "sys.maxsize". If the length is larger than
   "sys.maxsize" some features (such as "len()") may raise
   "OverflowError".  To prevent raising "OverflowError" by truth value
   testing, an object must define a "__bool__()" method.

object.__length_hint__(self)

   Called to implement "operator.length_hint()". Should return an
   estimated length for the object (which may be greater or less than
   the actual length). The length must be an integer ">=" 0. This
   method is purely an optimization and is never required for
   correctness.

   New in version 3.4.

Note: Slicing is done exclusively with the following three methods.
  A call like

     a[1:2] = b

  is translated to

     a[slice(1, 2, None)] = b

  and so forth.  Missing slice items are always filled in with "None".

object.__getitem__(self, key)

   Called to implement evaluation of "self[key]". For sequence types,
   the accepted keys should be integers and slice objects.  Note that
   the special interpretation of negative indexes (if the class wishes
   to emulate a sequence type) is up to the "__getitem__()" method. If
   *key* is of an inappropriate type, "TypeError" may be raised; if of
   a value outside the set of indexes for the sequence (after any
   special interpretation of negative values), "IndexError" should be
   raised. For mapping types, if *key* is missing (not in the
   container), "KeyError" should be raised.

   Note: "for" loops expect that an "IndexError" will be raised for
     illegal indexes to allow proper detection of the end of the
     sequence.

object.__missing__(self, key)

   Called by "dict"."__getitem__()" to implement "self[key]" for dict
   subclasses when key is not in the dictionary.

object.__setitem__(self, key, value)

   Called to implement assignment to "self[key]".  Same note as for
   "__getitem__()".  This should only be implemented for mappings if
   the objects support changes to the values for keys, or if new keys
   can be added, or for sequences if elements can be replaced.  The
   same exceptions should be raised for improper *key* values as for
   the "__getitem__()" method.

object.__delitem__(self, key)

   Called to implement deletion of "self[key]".  Same note as for
   "__getitem__()".  This should only be implemented for mappings if
   the objects support removal of keys, or for sequences if elements
   can be removed from the sequence.  The same exceptions should be
   raised for improper *key* values as for the "__getitem__()" method.

object.__iter__(self)

   This method is called when an iterator is required for a container.
   This method should return a new iterator object that can iterate
   over all the objects in the container.  For mappings, it should
   iterate over the keys of the container.

   Iterator objects also need to implement this method; they are
   required to return themselves.  For more information on iterator
   objects, see Iterator Types.

object.__reversed__(self)

   Called (if present) by the "reversed()" built-in to implement
   reverse iteration.  It should return a new iterator object that
   iterates over all the objects in the container in reverse order.

   If the "__reversed__()" method is not provided, the "reversed()"
   built-in will fall back to using the sequence protocol ("__len__()"
   and "__getitem__()").  Objects that support the sequence protocol
   should only provide "__reversed__()" if they can provide an
   implementation that is more efficient than the one provided by
   "reversed()".

The membership test operators ("in" and "not in") are normally
implemented as an iteration through a sequence.  However, container
objects can supply the following special method with a more efficient
implementation, which also does not require the object be a sequence.

object.__contains__(self, item)

   Called to implement membership test operators.  Should return true
   if *item* is in *self*, false otherwise.  For mapping objects, this
   should consider the keys of the mapping rather than the values or
   the key-item pairs.

   For objects that don't define "__contains__()", the membership test
   first tries iteration via "__iter__()", then the old sequence
   iteration protocol via "__getitem__()", see this section in the
   language reference.


Emulating numeric types
=======================

The following methods can be defined to emulate numeric objects.
Methods corresponding to operations that are not supported by the
particular kind of number implemented (e.g., bitwise operations for
non-integral numbers) should be left undefined.

object.__add__(self, other)
object.__sub__(self, other)
object.__mul__(self, other)
object.__matmul__(self, other)
object.__truediv__(self, other)
object.__floordiv__(self, other)
object.__mod__(self, other)
object.__divmod__(self, other)
object.__pow__(self, other[, modulo])
object.__lshift__(self, other)
object.__rshift__(self, other)
object.__and__(self, other)
object.__xor__(self, other)
object.__or__(self, other)

   These methods are called to implement the binary arithmetic
   operations ("+", "-", "*", "@", "/", "//", "%", "divmod()",
   "pow()", "**", "<<", ">>", "&", "^", "|").  For instance, to
   evaluate the expression "x + y", where *x* is an instance of a
   class that has an "__add__()" method, "x.__add__(y)" is called.
   The "__divmod__()" method should be the equivalent to using
   "__floordiv__()" and "__mod__()"; it should not be related to
   "__truediv__()".  Note that "__pow__()" should be defined to accept
   an optional third argument if the ternary version of the built-in
   "pow()" function is to be supported.

   If one of those methods does not support the operation with the
   supplied arguments, it should return "NotImplemented".

object.__radd__(self, other)
object.__rsub__(self, other)
object.__rmul__(self, other)
object.__rmatmul__(self, other)
object.__rtruediv__(self, other)
object.__rfloordiv__(self, other)
object.__rmod__(self, other)
object.__rdivmod__(self, other)
object.__rpow__(self, other)
object.__rlshift__(self, other)
object.__rrshift__(self, other)
object.__rand__(self, other)
object.__rxor__(self, other)
object.__ror__(self, other)

   These methods are called to implement the binary arithmetic
   operations ("+", "-", "*", "@", "/", "//", "%", "divmod()",
   "pow()", "**", "<<", ">>", "&", "^", "|") with reflected (swapped)
   operands.  These functions are only called if the left operand does
   not support the corresponding operation [3] and the operands are of
   different types. [4] For instance, to evaluate the expression "x -
   y", where *y* is an instance of a class that has an "__rsub__()"
   method, "y.__rsub__(x)" is called if "x.__sub__(y)" returns
   *NotImplemented*.

   Note that ternary "pow()" will not try calling "__rpow__()" (the
   coercion rules would become too complicated).

   Note: If the right operand's type is a subclass of the left
     operand's type and that subclass provides the reflected method
     for the operation, this method will be called before the left
     operand's non-reflected method.  This behavior allows subclasses
     to override their ancestors' operations.

object.__iadd__(self, other)
object.__isub__(self, other)
object.__imul__(self, other)
object.__imatmul__(self, other)
object.__itruediv__(self, other)
object.__ifloordiv__(self, other)
object.__imod__(self, other)
object.__ipow__(self, other[, modulo])
object.__ilshift__(self, other)
object.__irshift__(self, other)
object.__iand__(self, other)
object.__ixor__(self, other)
object.__ior__(self, other)

   These methods are called to implement the augmented arithmetic
   assignments ("+=", "-=", "*=", "@=", "/=", "//=", "%=", "**=",
   "<<=", ">>=", "&=", "^=", "|=").  These methods should attempt to
   do the operation in-place (modifying *self*) and return the result
   (which could be, but does not have to be, *self*).  If a specific
   method is not defined, the augmented assignment falls back to the
   normal methods.  For instance, if *x* is an instance of a class
   with an "__iadd__()" method, "x += y" is equivalent to "x =
   x.__iadd__(y)" . Otherwise, "x.__add__(y)" and "y.__radd__(x)" are
   considered, as with the evaluation of "x + y". In certain
   situations, augmented assignment can result in unexpected errors
   (see Why does a_tuple[i] += ['item'] raise an exception when the
   addition works?), but this behavior is in fact part of the data
   model.

object.__neg__(self)
object.__pos__(self)
object.__abs__(self)
object.__invert__(self)

   Called to implement the unary arithmetic operations ("-", "+",
   "abs()" and "~").

object.__complex__(self)
object.__int__(self)
object.__float__(self)
object.__round__(self[, n])

   Called to implement the built-in functions "complex()", "int()",
   "float()" and "round()".  Should return a value of the appropriate
   type.

object.__index__(self)

   Called to implement "operator.index()", and whenever Python needs
   to losslessly convert the numeric object to an integer object (such
   as in slicing, or in the built-in "bin()", "hex()" and "oct()"
   functions). Presence of this method indicates that the numeric
   object is an integer type.  Must return an integer.

   Note: In order to have a coherent integer type class, when
     "__index__()" is defined "__int__()" should also be defined, and
     both should return the same value.


With Statement Context Managers
===============================

A *context manager* is an object that defines the runtime context to
be established when executing a "with" statement. The context manager
handles the entry into, and the exit from, the desired runtime context
for the execution of the block of code.  Context managers are normally
invoked using the "with" statement (described in section The with
statement), but can also be used by directly invoking their methods.

Typical uses of context managers include saving and restoring various
kinds of global state, locking and unlocking resources, closing opened
files, etc.

For more information on context managers, see Context Manager Types.

object.__enter__(self)

   Enter the runtime context related to this object. The "with"
   statement will bind this method's return value to the target(s)
   specified in the "as" clause of the statement, if any.

object.__exit__(self, exc_type, exc_value, traceback)

   Exit the runtime context related to this object. The parameters
   describe the exception that caused the context to be exited. If the
   context was exited without an exception, all three arguments will
   be "None".

   If an exception is supplied, and the method wishes to suppress the
   exception (i.e., prevent it from being propagated), it should
   return a true value. Otherwise, the exception will be processed
   normally upon exit from this method.

   Note that "__exit__()" methods should not reraise the passed-in
   exception; this is the caller's responsibility.

See also:

  **PEP 343** - The "with" statement
     The specification, background, and examples for the Python "with"
     statement.


Special method lookup
=====================

For custom classes, implicit invocations of special methods are only
guaranteed to work correctly if defined on an object's type, not in
the object's instance dictionary.  That behaviour is the reason why
the following code raises an exception:

   >>> class C:
   ...     pass
   ...
   >>> c = C()
   >>> c.__len__ = lambda: 5
   >>> len(c)
   Traceback (most recent call last):
     File "<stdin>", line 1, in <module>
   TypeError: object of type 'C' has no len()

The rationale behind this behaviour lies with a number of special
methods such as "__hash__()" and "__repr__()" that are implemented by
all objects, including type objects. If the implicit lookup of these
methods used the conventional lookup process, they would fail when
invoked on the type object itself:

   >>> 1 .__hash__() == hash(1)
   True
   >>> int.__hash__() == hash(int)
   Traceback (most recent call last):
     File "<stdin>", line 1, in <module>
   TypeError: descriptor '__hash__' of 'int' object needs an argument

Incorrectly attempting to invoke an unbound method of a class in this
way is sometimes referred to as 'metaclass confusion', and is avoided
by bypassing the instance when looking up special methods:

   >>> type(1).__hash__(1) == hash(1)
   True
   >>> type(int).__hash__(int) == hash(int)
   True

In addition to bypassing any instance attributes in the interest of
correctness, implicit special method lookup generally also bypasses
the "__getattribute__()" method even of the object's metaclass:

   >>> class Meta(type):
   ...     def __getattribute__(*args):
   ...         print("Metaclass getattribute invoked")
   ...         return type.__getattribute__(*args)
   ...
   >>> class C(object, metaclass=Meta):
   ...     def __len__(self):
   ...         return 10
   ...     def __getattribute__(*args):
   ...         print("Class getattribute invoked")
   ...         return object.__getattribute__(*args)
   ...
   >>> c = C()
   >>> c.__len__()                 # Explicit lookup via instance
   Class getattribute invoked
   10
   >>> type(c).__len__(c)          # Explicit lookup via type
   Metaclass getattribute invoked
   10
   >>> len(c)                      # Implicit lookup
   10

Bypassing the "__getattribute__()" machinery in this fashion provides
significant scope for speed optimisations within the interpreter, at
the cost of some flexibility in the handling of special methods (the
special method *must* be set on the class object itself in order to be
consistently invoked by the interpreter).
"""
    , 'string-methods':
    """String Methods
**************

Strings implement all of the common sequence operations, along with
the additional methods described below.

Strings also support two styles of string formatting, one providing a
large degree of flexibility and customization (see "str.format()",
Format String Syntax and Custom String Formatting) and the other based
on C "printf" style formatting that handles a narrower range of types
and is slightly harder to use correctly, but is often faster for the
cases it can handle (printf-style String Formatting).

The Text Processing Services section of the standard library covers a
number of other modules that provide various text related utilities
(including regular expression support in the "re" module).

str.capitalize()

   Return a copy of the string with its first character capitalized
   and the rest lowercased.

str.casefold()

   Return a casefolded copy of the string. Casefolded strings may be
   used for caseless matching.

   Casefolding is similar to lowercasing but more aggressive because
   it is intended to remove all case distinctions in a string. For
   example, the German lowercase letter "'ß'" is equivalent to ""ss"".
   Since it is already lowercase, "lower()" would do nothing to "'ß'";
   "casefold()" converts it to ""ss"".

   The casefolding algorithm is described in section 3.13 of the
   Unicode Standard.

   New in version 3.3.

str.center(width[, fillchar])

   Return centered in a string of length *width*. Padding is done
   using the specified *fillchar* (default is an ASCII space). The
   original string is returned if *width* is less than or equal to
   "len(s)".

str.count(sub[, start[, end]])

   Return the number of non-overlapping occurrences of substring *sub*
   in the range [*start*, *end*].  Optional arguments *start* and
   *end* are interpreted as in slice notation.

str.encode(encoding="utf-8", errors="strict")

   Return an encoded version of the string as a bytes object. Default
   encoding is "'utf-8'". *errors* may be given to set a different
   error handling scheme. The default for *errors* is "'strict'",
   meaning that encoding errors raise a "UnicodeError". Other possible
   values are "'ignore'", "'replace'", "'xmlcharrefreplace'",
   "'backslashreplace'" and any other name registered via
   "codecs.register_error()", see section Error Handlers. For a list
   of possible encodings, see section Standard Encodings.

   Changed in version 3.1: Support for keyword arguments added.

str.endswith(suffix[, start[, end]])

   Return "True" if the string ends with the specified *suffix*,
   otherwise return "False".  *suffix* can also be a tuple of suffixes
   to look for.  With optional *start*, test beginning at that
   position.  With optional *end*, stop comparing at that position.

str.expandtabs(tabsize=8)

   Return a copy of the string where all tab characters are replaced
   by one or more spaces, depending on the current column and the
   given tab size.  Tab positions occur every *tabsize* characters
   (default is 8, giving tab positions at columns 0, 8, 16 and so on).
   To expand the string, the current column is set to zero and the
   string is examined character by character.  If the character is a
   tab ("\\t"), one or more space characters are inserted in the result
   until the current column is equal to the next tab position. (The
   tab character itself is not copied.)  If the character is a newline
   ("\\n") or return ("\\r"), it is copied and the current column is
   reset to zero.  Any other character is copied unchanged and the
   current column is incremented by one regardless of how the
   character is represented when printed.

   >>> '01\\t012\\t0123\\t01234'.expandtabs()
   '01      012     0123    01234'
   >>> '01\\t012\\t0123\\t01234'.expandtabs(4)
   '01  012 0123    01234'

str.find(sub[, start[, end]])

   Return the lowest index in the string where substring *sub* is
   found within the slice "s[start:end]".  Optional arguments *start*
   and *end* are interpreted as in slice notation.  Return "-1" if
   *sub* is not found.

   Note: The "find()" method should be used only if you need to know
     the position of *sub*.  To check if *sub* is a substring or not,
     use the "in" operator:

        >>> 'Py' in 'Python'
        True

str.format(*args, **kwargs)

   Perform a string formatting operation.  The string on which this
   method is called can contain literal text or replacement fields
   delimited by braces "{}".  Each replacement field contains either
   the numeric index of a positional argument, or the name of a
   keyword argument.  Returns a copy of the string where each
   replacement field is replaced with the string value of the
   corresponding argument.

   >>> "The sum of 1 + 2 is {0}".format(1+2)
   'The sum of 1 + 2 is 3'

   See Format String Syntax for a description of the various
   formatting options that can be specified in format strings.

str.format_map(mapping)

   Similar to "str.format(**mapping)", except that "mapping" is used
   directly and not copied to a "dict".  This is useful if for example
   "mapping" is a dict subclass:

   >>> class Default(dict):
   ...     def __missing__(self, key):
   ...         return key
   ...
   >>> '{name} was born in {country}'.format_map(Default(name='Guido'))
   'Guido was born in country'

   New in version 3.2.

str.index(sub[, start[, end]])

   Like "find()", but raise "ValueError" when the substring is not
   found.

str.isalnum()

   Return true if all characters in the string are alphanumeric and
   there is at least one character, false otherwise.  A character "c"
   is alphanumeric if one of the following returns "True":
   "c.isalpha()", "c.isdecimal()", "c.isdigit()", or "c.isnumeric()".

str.isalpha()

   Return true if all characters in the string are alphabetic and
   there is at least one character, false otherwise.  Alphabetic
   characters are those characters defined in the Unicode character
   database as "Letter", i.e., those with general category property
   being one of "Lm", "Lt", "Lu", "Ll", or "Lo".  Note that this is
   different from the "Alphabetic" property defined in the Unicode
   Standard.

str.isdecimal()

   Return true if all characters in the string are decimal characters
   and there is at least one character, false otherwise. Decimal
   characters are those that can be used to form numbers in base 10,
   e.g. U+0660, ARABIC-INDIC DIGIT ZERO.  Formally a decimal character
   is a character in the Unicode General Category "Nd".

str.isdigit()

   Return true if all characters in the string are digits and there is
   at least one character, false otherwise.  Digits include decimal
   characters and digits that need special handling, such as the
   compatibility superscript digits. This covers digits which cannot
   be used to form numbers in base 10, like the Kharosthi numbers.
   Formally, a digit is a character that has the property value
   Numeric_Type=Digit or Numeric_Type=Decimal.

str.isidentifier()

   Return true if the string is a valid identifier according to the
   language definition, section Identifiers and keywords.

   Use "keyword.iskeyword()" to test for reserved identifiers such as
   "def" and "class".

str.islower()

   Return true if all cased characters [4] in the string are lowercase
   and there is at least one cased character, false otherwise.

str.isnumeric()

   Return true if all characters in the string are numeric characters,
   and there is at least one character, false otherwise. Numeric
   characters include digit characters, and all characters that have
   the Unicode numeric value property, e.g. U+2155, VULGAR FRACTION
   ONE FIFTH.  Formally, numeric characters are those with the
   property value Numeric_Type=Digit, Numeric_Type=Decimal or
   Numeric_Type=Numeric.

str.isprintable()

   Return true if all characters in the string are printable or the
   string is empty, false otherwise.  Nonprintable characters are
   those characters defined in the Unicode character database as
   "Other" or "Separator", excepting the ASCII space (0x20) which is
   considered printable.  (Note that printable characters in this
   context are those which should not be escaped when "repr()" is
   invoked on a string.  It has no bearing on the handling of strings
   written to "sys.stdout" or "sys.stderr".)

str.isspace()

   Return true if there are only whitespace characters in the string
   and there is at least one character, false otherwise.  Whitespace
   characters  are those characters defined in the Unicode character
   database as "Other" or "Separator" and those with bidirectional
   property being one of "WS", "B", or "S".

str.istitle()

   Return true if the string is a titlecased string and there is at
   least one character, for example uppercase characters may only
   follow uncased characters and lowercase characters only cased ones.
   Return false otherwise.

str.isupper()

   Return true if all cased characters [4] in the string are uppercase
   and there is at least one cased character, false otherwise.

str.join(iterable)

   Return a string which is the concatenation of the strings in
   *iterable*. A "TypeError" will be raised if there are any non-
   string values in *iterable*, including "bytes" objects.  The
   separator between elements is the string providing this method.

str.ljust(width[, fillchar])

   Return the string left justified in a string of length *width*.
   Padding is done using the specified *fillchar* (default is an ASCII
   space). The original string is returned if *width* is less than or
   equal to "len(s)".

str.lower()

   Return a copy of the string with all the cased characters [4]
   converted to lowercase.

   The lowercasing algorithm used is described in section 3.13 of the
   Unicode Standard.

str.lstrip([chars])

   Return a copy of the string with leading characters removed.  The
   *chars* argument is a string specifying the set of characters to be
   removed.  If omitted or "None", the *chars* argument defaults to
   removing whitespace.  The *chars* argument is not a prefix; rather,
   all combinations of its values are stripped:

      >>> '   spacious   '.lstrip()
      'spacious   '
      >>> 'www.example.com'.lstrip('cmowz.')
      'example.com'

static str.maketrans(x[, y[, z]])

   This static method returns a translation table usable for
   "str.translate()".

   If there is only one argument, it must be a dictionary mapping
   Unicode ordinals (integers) or characters (strings of length 1) to
   Unicode ordinals, strings (of arbitrary lengths) or "None".
   Character keys will then be converted to ordinals.

   If there are two arguments, they must be strings of equal length,
   and in the resulting dictionary, each character in x will be mapped
   to the character at the same position in y.  If there is a third
   argument, it must be a string, whose characters will be mapped to
   "None" in the result.

str.partition(sep)

   Split the string at the first occurrence of *sep*, and return a
   3-tuple containing the part before the separator, the separator
   itself, and the part after the separator.  If the separator is not
   found, return a 3-tuple containing the string itself, followed by
   two empty strings.

str.replace(old, new[, count])

   Return a copy of the string with all occurrences of substring *old*
   replaced by *new*.  If the optional argument *count* is given, only
   the first *count* occurrences are replaced.

str.rfind(sub[, start[, end]])

   Return the highest index in the string where substring *sub* is
   found, such that *sub* is contained within "s[start:end]".
   Optional arguments *start* and *end* are interpreted as in slice
   notation.  Return "-1" on failure.

str.rindex(sub[, start[, end]])

   Like "rfind()" but raises "ValueError" when the substring *sub* is
   not found.

str.rjust(width[, fillchar])

   Return the string right justified in a string of length *width*.
   Padding is done using the specified *fillchar* (default is an ASCII
   space). The original string is returned if *width* is less than or
   equal to "len(s)".

str.rpartition(sep)

   Split the string at the last occurrence of *sep*, and return a
   3-tuple containing the part before the separator, the separator
   itself, and the part after the separator.  If the separator is not
   found, return a 3-tuple containing two empty strings, followed by
   the string itself.

str.rsplit(sep=None, maxsplit=-1)

   Return a list of the words in the string, using *sep* as the
   delimiter string. If *maxsplit* is given, at most *maxsplit* splits
   are done, the *rightmost* ones.  If *sep* is not specified or
   "None", any whitespace string is a separator.  Except for splitting
   from the right, "rsplit()" behaves like "split()" which is
   described in detail below.

str.rstrip([chars])

   Return a copy of the string with trailing characters removed.  The
   *chars* argument is a string specifying the set of characters to be
   removed.  If omitted or "None", the *chars* argument defaults to
   removing whitespace.  The *chars* argument is not a suffix; rather,
   all combinations of its values are stripped:

      >>> '   spacious   '.rstrip()
      '   spacious'
      >>> 'mississippi'.rstrip('ipz')
      'mississ'

str.split(sep=None, maxsplit=-1)

   Return a list of the words in the string, using *sep* as the
   delimiter string.  If *maxsplit* is given, at most *maxsplit*
   splits are done (thus, the list will have at most "maxsplit+1"
   elements).  If *maxsplit* is not specified or "-1", then there is
   no limit on the number of splits (all possible splits are made).

   If *sep* is given, consecutive delimiters are not grouped together
   and are deemed to delimit empty strings (for example,
   "'1,,2'.split(',')" returns "['1', '', '2']").  The *sep* argument
   may consist of multiple characters (for example,
   "'1<>2<>3'.split('<>')" returns "['1', '2', '3']"). Splitting an
   empty string with a specified separator returns "['']".

   For example:

      >>> '1,2,3'.split(',')
      ['1', '2', '3']
      >>> '1,2,3'.split(',', maxsplit=1)
      ['1', '2,3']
      >>> '1,2,,3,'.split(',')
      ['1', '2', '', '3', '']

   If *sep* is not specified or is "None", a different splitting
   algorithm is applied: runs of consecutive whitespace are regarded
   as a single separator, and the result will contain no empty strings
   at the start or end if the string has leading or trailing
   whitespace.  Consequently, splitting an empty string or a string
   consisting of just whitespace with a "None" separator returns "[]".

   For example:

      >>> '1 2 3'.split()
      ['1', '2', '3']
      >>> '1 2 3'.split(maxsplit=1)
      ['1', '2 3']
      >>> '   1   2   3   '.split()
      ['1', '2', '3']

str.splitlines([keepends])

   Return a list of the lines in the string, breaking at line
   boundaries.  Line breaks are not included in the resulting list
   unless *keepends* is given and true.

   This method splits on the following line boundaries.  In
   particular, the boundaries are a superset of *universal newlines*.

   +-------------------------+-------------------------------+
   | Representation          | Description                   |
   +=========================+===============================+
   | "\\n"                    | Line Feed                     |
   +-------------------------+-------------------------------+
   | "\\r"                    | Carriage Return               |
   +-------------------------+-------------------------------+
   | "\\r\\n"                  | Carriage Return + Line Feed   |
   +-------------------------+-------------------------------+
   | "\\v" or "\\x0b"          | Line Tabulation               |
   +-------------------------+-------------------------------+
   | "\\f" or "\\x0c"          | Form Feed                     |
   +-------------------------+-------------------------------+
   | "\\x1c"                  | File Separator                |
   +-------------------------+-------------------------------+
   | "\\x1d"                  | Group Separator               |
   +-------------------------+-------------------------------+
   | "\\x1e"                  | Record Separator              |
   +-------------------------+-------------------------------+
   | "\\x85"                  | Next Line (C1 Control Code)   |
   +-------------------------+-------------------------------+
   | "\\u2028"                | Line Separator                |
   +-------------------------+-------------------------------+
   | "\\u2029"                | Paragraph Separator           |
   +-------------------------+-------------------------------+

   Changed in version 3.2: "\\v" and "\\f" added to list of line
   boundaries.

   For example:

      >>> 'ab c\\n\\nde fg\\rkl\\r\\n'.splitlines()
      ['ab c', '', 'de fg', 'kl']
      >>> 'ab c\\n\\nde fg\\rkl\\r\\n'.splitlines(keepends=True)
      ['ab c\\n', '\\n', 'de fg\\r', 'kl\\r\\n']

   Unlike "split()" when a delimiter string *sep* is given, this
   method returns an empty list for the empty string, and a terminal
   line break does not result in an extra line:

      >>> "".splitlines()
      []
      >>> "One line\\n".splitlines()
      ['One line']

   For comparison, "split('\\n')" gives:

      >>> ''.split('\\n')
      ['']
      >>> 'Two lines\\n'.split('\\n')
      ['Two lines', '']

str.startswith(prefix[, start[, end]])

   Return "True" if string starts with the *prefix*, otherwise return
   "False". *prefix* can also be a tuple of prefixes to look for.
   With optional *start*, test string beginning at that position.
   With optional *end*, stop comparing string at that position.

str.strip([chars])

   Return a copy of the string with the leading and trailing
   characters removed. The *chars* argument is a string specifying the
   set of characters to be removed. If omitted or "None", the *chars*
   argument defaults to removing whitespace. The *chars* argument is
   not a prefix or suffix; rather, all combinations of its values are
   stripped:

      >>> '   spacious   '.strip()
      'spacious'
      >>> 'www.example.com'.strip('cmowz.')
      'example'

   The outermost leading and trailing *chars* argument values are
   stripped from the string. Characters are removed from the leading
   end until reaching a string character that is not contained in the
   set of characters in *chars*. A similar action takes place on the
   trailing end. For example:

      >>> comment_string = '#....... Section 3.2.1 Issue #32 .......'
      >>> comment_string.strip('.#! ')
      'Section 3.2.1 Issue #32'

str.swapcase()

   Return a copy of the string with uppercase characters converted to
   lowercase and vice versa. Note that it is not necessarily true that
   "s.swapcase().swapcase() == s".

str.title()

   Return a titlecased version of the string where words start with an
   uppercase character and the remaining characters are lowercase.

   For example:

      >>> 'Hello world'.title()
      'Hello World'

   The algorithm uses a simple language-independent definition of a
   word as groups of consecutive letters.  The definition works in
   many contexts but it means that apostrophes in contractions and
   possessives form word boundaries, which may not be the desired
   result:

      >>> "they're bill's friends from the UK".title()
      "They'Re Bill'S Friends From The Uk"

   A workaround for apostrophes can be constructed using regular
   expressions:

      >>> import re
      >>> def titlecase(s):
      ...     return re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
      ...                   lambda mo: mo.group(0)[0].upper() +
      ...                              mo.group(0)[1:].lower(),
      ...                   s)
      ...
      >>> titlecase("they're bill's friends.")
      "They're Bill's Friends."

str.translate(table)

   Return a copy of the string in which each character has been mapped
   through the given translation table.  The table must be an object
   that implements indexing via "__getitem__()", typically a *mapping*
   or *sequence*.  When indexed by a Unicode ordinal (an integer), the
   table object can do any of the following: return a Unicode ordinal
   or a string, to map the character to one or more other characters;
   return "None", to delete the character from the return string; or
   raise a "LookupError" exception, to map the character to itself.

   You can use "str.maketrans()" to create a translation map from
   character-to-character mappings in different formats.

   See also the "codecs" module for a more flexible approach to custom
   character mappings.

str.upper()

   Return a copy of the string with all the cased characters [4]
   converted to uppercase.  Note that "str.upper().isupper()" might be
   "False" if "s" contains uncased characters or if the Unicode
   category of the resulting character(s) is not "Lu" (Letter,
   uppercase), but e.g. "Lt" (Letter, titlecase).

   The uppercasing algorithm used is described in section 3.13 of the
   Unicode Standard.

str.zfill(width)

   Return a copy of the string left filled with ASCII "'0'" digits to
   make a string of length *width*. A leading sign prefix
   ("'+'"/"'-'") is handled by inserting the padding *after* the sign
   character rather than before. The original string is returned if
   *width* is less than or equal to "len(s)".

   For example:

      >>> "42".zfill(5)
      '00042'
      >>> "-42".zfill(5)
      '-0042'
"""
    , 'strings':
    """String and Bytes literals
*************************

String literals are described by the following lexical definitions:

   stringliteral   ::= [stringprefix](shortstring | longstring)
   stringprefix    ::= "r" | "u" | "R" | "U" | "f" | "F"
                    | "fr" | "Fr" | "fR" | "FR" | "rf" | "rF" | "Rf" | "RF"
   shortstring     ::= "'" shortstringitem* "'" | '"' shortstringitem* '"'
   longstring      ::= "'''" longstringitem* "'''" | '""\"' longstringitem* '""\"'
   shortstringitem ::= shortstringchar | stringescapeseq
   longstringitem  ::= longstringchar | stringescapeseq
   shortstringchar ::= <any source character except "\\" or newline or the quote>
   longstringchar  ::= <any source character except "\\">
   stringescapeseq ::= "\\" <any source character>

   bytesliteral   ::= bytesprefix(shortbytes | longbytes)
   bytesprefix    ::= "b" | "B" | "br" | "Br" | "bR" | "BR" | "rb" | "rB" | "Rb" | "RB"
   shortbytes     ::= "'" shortbytesitem* "'" | '"' shortbytesitem* '"'
   longbytes      ::= "'''" longbytesitem* "'''" | '""\"' longbytesitem* '""\"'
   shortbytesitem ::= shortbyteschar | bytesescapeseq
   longbytesitem  ::= longbyteschar | bytesescapeseq
   shortbyteschar ::= <any ASCII character except "\\" or newline or the quote>
   longbyteschar  ::= <any ASCII character except "\\">
   bytesescapeseq ::= "\\" <any ASCII character>

One syntactic restriction not indicated by these productions is that
whitespace is not allowed between the "stringprefix" or "bytesprefix"
and the rest of the literal. The source character set is defined by
the encoding declaration; it is UTF-8 if no encoding declaration is
given in the source file; see section Encoding declarations.

In plain English: Both types of literals can be enclosed in matching
single quotes ("'") or double quotes (""\").  They can also be enclosed
in matching groups of three single or double quotes (these are
generally referred to as *triple-quoted strings*).  The backslash
("\\") character is used to escape characters that otherwise have a
special meaning, such as newline, backslash itself, or the quote
character.

Bytes literals are always prefixed with "'b'" or "'B'"; they produce
an instance of the "bytes" type instead of the "str" type.  They may
only contain ASCII characters; bytes with a numeric value of 128 or
greater must be expressed with escapes.

As of Python 3.3 it is possible again to prefix string literals with a
"u" prefix to simplify maintenance of dual 2.x and 3.x codebases.

Both string and bytes literals may optionally be prefixed with a
letter "'r'" or "'R'"; such strings are called *raw strings* and treat
backslashes as literal characters.  As a result, in string literals,
"'\\U'" and "'\\u'" escapes in raw strings are not treated specially.
Given that Python 2.x's raw unicode literals behave differently than
Python 3.x's the "'ur'" syntax is not supported.

New in version 3.3: The "'rb'" prefix of raw bytes literals has been
added as a synonym of "'br'".

New in version 3.3: Support for the unicode legacy literal
("u'value'") was reintroduced to simplify the maintenance of dual
Python 2.x and 3.x codebases. See **PEP 414** for more information.

A string literal with "'f'" or "'F'" in its prefix is a *formatted
string literal*; see Formatted string literals.  The "'f'" may be
combined with "'r'", but not with "'b'" or "'u'", therefore raw
formatted strings are possible, but formatted bytes literals are not.

In triple-quoted literals, unescaped newlines and quotes are allowed
(and are retained), except that three unescaped quotes in a row
terminate the literal.  (A "quote" is the character used to open the
literal, i.e. either "'" or ""\".)

Unless an "'r'" or "'R'" prefix is present, escape sequences in string
and bytes literals are interpreted according to rules similar to those
used by Standard C.  The recognized escape sequences are:

+-------------------+-----------------------------------+---------+
| Escape Sequence   | Meaning                           | Notes   |
+===================+===================================+=========+
| "\\newline"        | Backslash and newline ignored     |         |
+-------------------+-----------------------------------+---------+
| "\\\\"              | Backslash ("\\")                   |         |
+-------------------+-----------------------------------+---------+
| "\\'"              | Single quote ("'")                |         |
+-------------------+-----------------------------------+---------+
| "\\""              | Double quote (""\")                |         |
+-------------------+-----------------------------------+---------+
| "\\a"              | ASCII Bell (BEL)                  |         |
+-------------------+-----------------------------------+---------+
| "\\b"              | ASCII Backspace (BS)              |         |
+-------------------+-----------------------------------+---------+
| "\\f"              | ASCII Formfeed (FF)               |         |
+-------------------+-----------------------------------+---------+
| "\\n"              | ASCII Linefeed (LF)               |         |
+-------------------+-----------------------------------+---------+
| "\\r"              | ASCII Carriage Return (CR)        |         |
+-------------------+-----------------------------------+---------+
| "\\t"              | ASCII Horizontal Tab (TAB)        |         |
+-------------------+-----------------------------------+---------+
| "\\v"              | ASCII Vertical Tab (VT)           |         |
+-------------------+-----------------------------------+---------+
| "\\ooo"            | Character with octal value *ooo*  | (1,3)   |
+-------------------+-----------------------------------+---------+
| "\\xhh"            | Character with hex value *hh*     | (2,3)   |
+-------------------+-----------------------------------+---------+

Escape sequences only recognized in string literals are:

+-------------------+-----------------------------------+---------+
| Escape Sequence   | Meaning                           | Notes   |
+===================+===================================+=========+
| "\\N{name}"        | Character named *name* in the     | (4)     |
|                   | Unicode database                  |         |
+-------------------+-----------------------------------+---------+
| "\\uxxxx"          | Character with 16-bit hex value   | (5)     |
|                   | *xxxx*                            |         |
+-------------------+-----------------------------------+---------+
| "\\Uxxxxxxxx"      | Character with 32-bit hex value   | (6)     |
|                   | *xxxxxxxx*                        |         |
+-------------------+-----------------------------------+---------+

Notes:

1. As in Standard C, up to three octal digits are accepted.

2. Unlike in Standard C, exactly two hex digits are required.

3. In a bytes literal, hexadecimal and octal escapes denote the
   byte with the given value. In a string literal, these escapes
   denote a Unicode character with the given value.

4. Changed in version 3.3: Support for name aliases [1] has been
   added.

5. Exactly four hex digits are required.

6. Any Unicode character can be encoded this way.  Exactly eight
   hex digits are required.

Unlike Standard C, all unrecognized escape sequences are left in the
string unchanged, i.e., *the backslash is left in the result*.  (This
behavior is useful when debugging: if an escape sequence is mistyped,
the resulting output is more easily recognized as broken.)  It is also
important to note that the escape sequences only recognized in string
literals fall into the category of unrecognized escapes for bytes
literals.

   Changed in version 3.6: Unrecognized escape sequences produce a
   DeprecationWarning.  In some future version of Python they will be
   a SyntaxError.

Even in a raw literal, quotes can be escaped with a backslash, but the
backslash remains in the result; for example, "r"\\""\" is a valid
string literal consisting of two characters: a backslash and a double
quote; "r"\\"" is not a valid string literal (even a raw string cannot
end in an odd number of backslashes).  Specifically, *a raw literal
cannot end in a single backslash* (since the backslash would escape
the following quote character).  Note also that a single backslash
followed by a newline is interpreted as those two characters as part
of the literal, *not* as a line continuation.
"""
    , 'subscriptions':
    """Subscriptions
*************

A subscription selects an item of a sequence (string, tuple or list)
or mapping (dictionary) object:

   subscription ::= primary "[" expression_list "]"

The primary must evaluate to an object that supports subscription
(lists or dictionaries for example).  User-defined objects can support
subscription by defining a "__getitem__()" method.

For built-in objects, there are two types of objects that support
subscription:

If the primary is a mapping, the expression list must evaluate to an
object whose value is one of the keys of the mapping, and the
subscription selects the value in the mapping that corresponds to that
key.  (The expression list is a tuple except if it has exactly one
item.)

If the primary is a sequence, the expression (list) must evaluate to
an integer or a slice (as discussed in the following section).

The formal syntax makes no special provision for negative indices in
sequences; however, built-in sequences all provide a "__getitem__()"
method that interprets negative indices by adding the length of the
sequence to the index (so that "x[-1]" selects the last item of "x").
The resulting value must be a nonnegative integer less than the number
of items in the sequence, and the subscription selects the item whose
index is that value (counting from zero). Since the support for
negative indices and slicing occurs in the object's "__getitem__()"
method, subclasses overriding this method will need to explicitly add
that support.

A string's items are characters.  A character is not a separate data
type but a string of exactly one character.
"""
    , 'truth':
    """Truth Value Testing
*******************

Any object can be tested for truth value, for use in an "if" or
"while" condition or as operand of the Boolean operations below. The
following values are considered false:

* "None"

* "False"

* zero of any numeric type, for example, "0", "0.0", "0j".

* any empty sequence, for example, "''", "()", "[]".

* any empty mapping, for example, "{}".

* instances of user-defined classes, if the class defines a
  "__bool__()" or "__len__()" method, when that method returns the
  integer zero or "bool" value "False". [1]

All other values are considered true --- so objects of many types are
always true.

Operations and built-in functions that have a Boolean result always
return "0" or "False" for false and "1" or "True" for true, unless
otherwise stated. (Important exception: the Boolean operations "or"
and "and" always return one of their operands.)
"""
    , 'try':
    """The "try" statement
*******************

The "try" statement specifies exception handlers and/or cleanup code
for a group of statements:

   try_stmt  ::= try1_stmt | try2_stmt
   try1_stmt ::= "try" ":" suite
                 ("except" [expression ["as" identifier]] ":" suite)+
                 ["else" ":" suite]
                 ["finally" ":" suite]
   try2_stmt ::= "try" ":" suite
                 "finally" ":" suite

The "except" clause(s) specify one or more exception handlers. When no
exception occurs in the "try" clause, no exception handler is
executed. When an exception occurs in the "try" suite, a search for an
exception handler is started.  This search inspects the except clauses
in turn until one is found that matches the exception.  An expression-
less except clause, if present, must be last; it matches any
exception.  For an except clause with an expression, that expression
is evaluated, and the clause matches the exception if the resulting
object is "compatible" with the exception.  An object is compatible
with an exception if it is the class or a base class of the exception
object or a tuple containing an item compatible with the exception.

If no except clause matches the exception, the search for an exception
handler continues in the surrounding code and on the invocation stack.
[1]

If the evaluation of an expression in the header of an except clause
raises an exception, the original search for a handler is canceled and
a search starts for the new exception in the surrounding code and on
the call stack (it is treated as if the entire "try" statement raised
the exception).

When a matching except clause is found, the exception is assigned to
the target specified after the "as" keyword in that except clause, if
present, and the except clause's suite is executed.  All except
clauses must have an executable block.  When the end of this block is
reached, execution continues normally after the entire try statement.
(This means that if two nested handlers exist for the same exception,
and the exception occurs in the try clause of the inner handler, the
outer handler will not handle the exception.)

When an exception has been assigned using "as target", it is cleared
at the end of the except clause.  This is as if

   except E as N:
       foo

was translated to

   except E as N:
       try:
           foo
       finally:
           del N

This means the exception must be assigned to a different name to be
able to refer to it after the except clause.  Exceptions are cleared
because with the traceback attached to them, they form a reference
cycle with the stack frame, keeping all locals in that frame alive
until the next garbage collection occurs.

Before an except clause's suite is executed, details about the
exception are stored in the "sys" module and can be accessed via
"sys.exc_info()". "sys.exc_info()" returns a 3-tuple consisting of the
exception class, the exception instance and a traceback object (see
section The standard type hierarchy) identifying the point in the
program where the exception occurred.  "sys.exc_info()" values are
restored to their previous values (before the call) when returning
from a function that handled an exception.

The optional "else" clause is executed if and when control flows off
the end of the "try" clause. [2] Exceptions in the "else" clause are
not handled by the preceding "except" clauses.

If "finally" is present, it specifies a 'cleanup' handler.  The "try"
clause is executed, including any "except" and "else" clauses.  If an
exception occurs in any of the clauses and is not handled, the
exception is temporarily saved. The "finally" clause is executed.  If
there is a saved exception it is re-raised at the end of the "finally"
clause.  If the "finally" clause raises another exception, the saved
exception is set as the context of the new exception. If the "finally"
clause executes a "return" or "break" statement, the saved exception
is discarded:

   >>> def f():
   ...     try:
   ...         1/0
   ...     finally:
   ...         return 42
   ...
   >>> f()
   42

The exception information is not available to the program during
execution of the "finally" clause.

When a "return", "break" or "continue" statement is executed in the
"try" suite of a "try"..."finally" statement, the "finally" clause is
also executed 'on the way out.' A "continue" statement is illegal in
the "finally" clause. (The reason is a problem with the current
implementation --- this restriction may be lifted in the future).

The return value of a function is determined by the last "return"
statement executed.  Since the "finally" clause always executes, a
"return" statement executed in the "finally" clause will always be the
last one executed:

   >>> def foo():
   ...     try:
   ...         return 'try'
   ...     finally:
   ...         return 'finally'
   ...
   >>> foo()
   'finally'

Additional information on exceptions can be found in section
Exceptions, and information on using the "raise" statement to generate
exceptions may be found in section The raise statement.
"""
    , 'types':
    """The standard type hierarchy
***************************

Below is a list of the types that are built into Python.  Extension
modules (written in C, Java, or other languages, depending on the
implementation) can define additional types.  Future versions of
Python may add types to the type hierarchy (e.g., rational numbers,
efficiently stored arrays of integers, etc.), although such additions
will often be provided via the standard library instead.

Some of the type descriptions below contain a paragraph listing
'special attributes.'  These are attributes that provide access to the
implementation and are not intended for general use.  Their definition
may change in the future.

None
   This type has a single value.  There is a single object with this
   value. This object is accessed through the built-in name "None". It
   is used to signify the absence of a value in many situations, e.g.,
   it is returned from functions that don't explicitly return
   anything. Its truth value is false.

NotImplemented
   This type has a single value.  There is a single object with this
   value. This object is accessed through the built-in name
   "NotImplemented". Numeric methods and rich comparison methods
   should return this value if they do not implement the operation for
   the operands provided.  (The interpreter will then try the
   reflected operation, or some other fallback, depending on the
   operator.)  Its truth value is true.

   See Implementing the arithmetic operations for more details.

Ellipsis
   This type has a single value.  There is a single object with this
   value. This object is accessed through the literal "..." or the
   built-in name "Ellipsis".  Its truth value is true.

"numbers.Number"
   These are created by numeric literals and returned as results by
   arithmetic operators and arithmetic built-in functions.  Numeric
   objects are immutable; once created their value never changes.
   Python numbers are of course strongly related to mathematical
   numbers, but subject to the limitations of numerical representation
   in computers.

   Python distinguishes between integers, floating point numbers, and
   complex numbers:

   "numbers.Integral"
      These represent elements from the mathematical set of integers
      (positive and negative).

      There are two types of integers:

      Integers ("int")

         These represent numbers in an unlimited range, subject to
         available (virtual) memory only.  For the purpose of shift
         and mask operations, a binary representation is assumed, and
         negative numbers are represented in a variant of 2's
         complement which gives the illusion of an infinite string of
         sign bits extending to the left.

      Booleans ("bool")
         These represent the truth values False and True.  The two
         objects representing the values "False" and "True" are the
         only Boolean objects. The Boolean type is a subtype of the
         integer type, and Boolean values behave like the values 0 and
         1, respectively, in almost all contexts, the exception being
         that when converted to a string, the strings ""False"" or
         ""True"" are returned, respectively.

      The rules for integer representation are intended to give the
      most meaningful interpretation of shift and mask operations
      involving negative integers.

   "numbers.Real" ("float")
      These represent machine-level double precision floating point
      numbers. You are at the mercy of the underlying machine
      architecture (and C or Java implementation) for the accepted
      range and handling of overflow. Python does not support single-
      precision floating point numbers; the savings in processor and
      memory usage that are usually the reason for using these are
      dwarfed by the overhead of using objects in Python, so there is
      no reason to complicate the language with two kinds of floating
      point numbers.

   "numbers.Complex" ("complex")
      These represent complex numbers as a pair of machine-level
      double precision floating point numbers.  The same caveats apply
      as for floating point numbers. The real and imaginary parts of a
      complex number "z" can be retrieved through the read-only
      attributes "z.real" and "z.imag".

Sequences
   These represent finite ordered sets indexed by non-negative
   numbers. The built-in function "len()" returns the number of items
   of a sequence. When the length of a sequence is *n*, the index set
   contains the numbers 0, 1, ..., *n*-1.  Item *i* of sequence *a* is
   selected by "a[i]".

   Sequences also support slicing: "a[i:j]" selects all items with
   index *k* such that *i* "<=" *k* "<" *j*.  When used as an
   expression, a slice is a sequence of the same type.  This implies
   that the index set is renumbered so that it starts at 0.

   Some sequences also support "extended slicing" with a third "step"
   parameter: "a[i:j:k]" selects all items of *a* with index *x* where
   "x = i + n*k", *n* ">=" "0" and *i* "<=" *x* "<" *j*.

   Sequences are distinguished according to their mutability:

   Immutable sequences
      An object of an immutable sequence type cannot change once it is
      created.  (If the object contains references to other objects,
      these other objects may be mutable and may be changed; however,
      the collection of objects directly referenced by an immutable
      object cannot change.)

      The following types are immutable sequences:

      Strings
         A string is a sequence of values that represent Unicode code
         points. All the code points in the range "U+0000 - U+10FFFF"
         can be represented in a string.  Python doesn't have a "char"
         type; instead, every code point in the string is represented
         as a string object with length "1".  The built-in function
         "ord()" converts a code point from its string form to an
         integer in the range "0 - 10FFFF"; "chr()" converts an
         integer in the range "0 - 10FFFF" to the corresponding length
         "1" string object. "str.encode()" can be used to convert a
         "str" to "bytes" using the given text encoding, and
         "bytes.decode()" can be used to achieve the opposite.

      Tuples
         The items of a tuple are arbitrary Python objects. Tuples of
         two or more items are formed by comma-separated lists of
         expressions.  A tuple of one item (a 'singleton') can be
         formed by affixing a comma to an expression (an expression by
         itself does not create a tuple, since parentheses must be
         usable for grouping of expressions).  An empty tuple can be
         formed by an empty pair of parentheses.

      Bytes
         A bytes object is an immutable array.  The items are 8-bit
         bytes, represented by integers in the range 0 <= x < 256.
         Bytes literals (like "b'abc'") and the built-in "bytes()"
         constructor can be used to create bytes objects.  Also, bytes
         objects can be decoded to strings via the "decode()" method.

   Mutable sequences
      Mutable sequences can be changed after they are created.  The
      subscription and slicing notations can be used as the target of
      assignment and "del" (delete) statements.

      There are currently two intrinsic mutable sequence types:

      Lists
         The items of a list are arbitrary Python objects.  Lists are
         formed by placing a comma-separated list of expressions in
         square brackets. (Note that there are no special cases needed
         to form lists of length 0 or 1.)

      Byte Arrays
         A bytearray object is a mutable array. They are created by
         the built-in "bytearray()" constructor.  Aside from being
         mutable (and hence unhashable), byte arrays otherwise provide
         the same interface and functionality as immutable "bytes"
         objects.

      The extension module "array" provides an additional example of a
      mutable sequence type, as does the "collections" module.

Set types
   These represent unordered, finite sets of unique, immutable
   objects. As such, they cannot be indexed by any subscript. However,
   they can be iterated over, and the built-in function "len()"
   returns the number of items in a set. Common uses for sets are fast
   membership testing, removing duplicates from a sequence, and
   computing mathematical operations such as intersection, union,
   difference, and symmetric difference.

   For set elements, the same immutability rules apply as for
   dictionary keys. Note that numeric types obey the normal rules for
   numeric comparison: if two numbers compare equal (e.g., "1" and
   "1.0"), only one of them can be contained in a set.

   There are currently two intrinsic set types:

   Sets
      These represent a mutable set. They are created by the built-in
      "set()" constructor and can be modified afterwards by several
      methods, such as "add()".

   Frozen sets
      These represent an immutable set.  They are created by the
      built-in "frozenset()" constructor.  As a frozenset is immutable
      and *hashable*, it can be used again as an element of another
      set, or as a dictionary key.

Mappings
   These represent finite sets of objects indexed by arbitrary index
   sets. The subscript notation "a[k]" selects the item indexed by "k"
   from the mapping "a"; this can be used in expressions and as the
   target of assignments or "del" statements. The built-in function
   "len()" returns the number of items in a mapping.

   There is currently a single intrinsic mapping type:

   Dictionaries
      These represent finite sets of objects indexed by nearly
      arbitrary values.  The only types of values not acceptable as
      keys are values containing lists or dictionaries or other
      mutable types that are compared by value rather than by object
      identity, the reason being that the efficient implementation of
      dictionaries requires a key's hash value to remain constant.
      Numeric types used for keys obey the normal rules for numeric
      comparison: if two numbers compare equal (e.g., "1" and "1.0")
      then they can be used interchangeably to index the same
      dictionary entry.

      Dictionaries are mutable; they can be created by the "{...}"
      notation (see section Dictionary displays).

      The extension modules "dbm.ndbm" and "dbm.gnu" provide
      additional examples of mapping types, as does the "collections"
      module.

Callable types
   These are the types to which the function call operation (see
   section Calls) can be applied:

   User-defined functions
      A user-defined function object is created by a function
      definition (see section Function definitions).  It should be
      called with an argument list containing the same number of items
      as the function's formal parameter list.

      Special attributes:

      +---------------------------+---------------------------------+-------------+
      | Attribute                 | Meaning                         |             |
      +===========================+=================================+=============+
      | "__doc__"                 | The function's documentation    | Writable    |
      |                           | string, or "None" if            |             |
      |                           | unavailable; not inherited by   |             |
      |                           | subclasses                      |             |
      +---------------------------+---------------------------------+-------------+
      | "__name__"                | The function's name             | Writable    |
      +---------------------------+---------------------------------+-------------+
      | "__qualname__"            | The function's *qualified name* | Writable    |
      |                           | New in version 3.3.             |             |
      +---------------------------+---------------------------------+-------------+
      | "__module__"              | The name of the module the      | Writable    |
      |                           | function was defined in, or     |             |
      |                           | "None" if unavailable.          |             |
      +---------------------------+---------------------------------+-------------+
      | "__defaults__"            | A tuple containing default      | Writable    |
      |                           | argument values for those       |             |
      |                           | arguments that have defaults,   |             |
      |                           | or "None" if no arguments have  |             |
      |                           | a default value                 |             |
      +---------------------------+---------------------------------+-------------+
      | "__code__"                | The code object representing    | Writable    |
      |                           | the compiled function body.     |             |
      +---------------------------+---------------------------------+-------------+
      | "__globals__"             | A reference to the dictionary   | Read-only   |
      |                           | that holds the function's       |             |
      |                           | global variables --- the global |             |
      |                           | namespace of the module in      |             |
      |                           | which the function was defined. |             |
      +---------------------------+---------------------------------+-------------+
      | "__dict__"                | The namespace supporting        | Writable    |
      |                           | arbitrary function attributes.  |             |
      +---------------------------+---------------------------------+-------------+
      | "__closure__"             | "None" or a tuple of cells that | Read-only   |
      |                           | contain bindings for the        |             |
      |                           | function's free variables.      |             |
      +---------------------------+---------------------------------+-------------+
      | "__annotations__"         | A dict containing annotations   | Writable    |
      |                           | of parameters.  The keys of the |             |
      |                           | dict are the parameter names,   |             |
      |                           | and "'return'" for the return   |             |
      |                           | annotation, if provided.        |             |
      +---------------------------+---------------------------------+-------------+
      | "__kwdefaults__"          | A dict containing defaults for  | Writable    |
      |                           | keyword-only parameters.        |             |
      +---------------------------+---------------------------------+-------------+

      Most of the attributes labelled "Writable" check the type of the
      assigned value.

      Function objects also support getting and setting arbitrary
      attributes, which can be used, for example, to attach metadata
      to functions.  Regular attribute dot-notation is used to get and
      set such attributes. *Note that the current implementation only
      supports function attributes on user-defined functions. Function
      attributes on built-in functions may be supported in the
      future.*

      Additional information about a function's definition can be
      retrieved from its code object; see the description of internal
      types below.

   Instance methods
      An instance method object combines a class, a class instance and
      any callable object (normally a user-defined function).

      Special read-only attributes: "__self__" is the class instance
      object, "__func__" is the function object; "__doc__" is the
      method's documentation (same as "__func__.__doc__"); "__name__"
      is the method name (same as "__func__.__name__"); "__module__"
      is the name of the module the method was defined in, or "None"
      if unavailable.

      Methods also support accessing (but not setting) the arbitrary
      function attributes on the underlying function object.

      User-defined method objects may be created when getting an
      attribute of a class (perhaps via an instance of that class), if
      that attribute is a user-defined function object or a class
      method object.

      When an instance method object is created by retrieving a user-
      defined function object from a class via one of its instances,
      its "__self__" attribute is the instance, and the method object
      is said to be bound.  The new method's "__func__" attribute is
      the original function object.

      When a user-defined method object is created by retrieving
      another method object from a class or instance, the behaviour is
      the same as for a function object, except that the "__func__"
      attribute of the new instance is not the original method object
      but its "__func__" attribute.

      When an instance method object is created by retrieving a class
      method object from a class or instance, its "__self__" attribute
      is the class itself, and its "__func__" attribute is the
      function object underlying the class method.

      When an instance method object is called, the underlying
      function ("__func__") is called, inserting the class instance
      ("__self__") in front of the argument list.  For instance, when
      "C" is a class which contains a definition for a function "f()",
      and "x" is an instance of "C", calling "x.f(1)" is equivalent to
      calling "C.f(x, 1)".

      When an instance method object is derived from a class method
      object, the "class instance" stored in "__self__" will actually
      be the class itself, so that calling either "x.f(1)" or "C.f(1)"
      is equivalent to calling "f(C,1)" where "f" is the underlying
      function.

      Note that the transformation from function object to instance
      method object happens each time the attribute is retrieved from
      the instance.  In some cases, a fruitful optimization is to
      assign the attribute to a local variable and call that local
      variable. Also notice that this transformation only happens for
      user-defined functions; other callable objects (and all non-
      callable objects) are retrieved without transformation.  It is
      also important to note that user-defined functions which are
      attributes of a class instance are not converted to bound
      methods; this *only* happens when the function is an attribute
      of the class.

   Generator functions
      A function or method which uses the "yield" statement (see
      section The yield statement) is called a *generator function*.
      Such a function, when called, always returns an iterator object
      which can be used to execute the body of the function:  calling
      the iterator's "iterator.__next__()" method will cause the
      function to execute until it provides a value using the "yield"
      statement.  When the function executes a "return" statement or
      falls off the end, a "StopIteration" exception is raised and the
      iterator will have reached the end of the set of values to be
      returned.

   Coroutine functions
      A function or method which is defined using "async def" is
      called a *coroutine function*.  Such a function, when called,
      returns a *coroutine* object.  It may contain "await"
      expressions, as well as "async with" and "async for" statements.
      See also the Coroutine Objects section.

   Asynchronous generator functions
      A function or method which is defined using "async def" and
      which uses the "yield" statement is called a *asynchronous
      generator function*.  Such a function, when called, returns an
      asynchronous iterator object which can be used in an "async for"
      statement to execute the body of the function.

      Calling the asynchronous iterator's "aiterator.__anext__()"
      method will return an *awaitable* which when awaited will
      execute until it provides a value using the "yield" expression.
      When the function executes an empty "return" statement or falls
      off the end, a "StopAsyncIteration" exception is raised and the
      asynchronous iterator will have reached the end of the set of
      values to be yielded.

   Built-in functions
      A built-in function object is a wrapper around a C function.
      Examples of built-in functions are "len()" and "math.sin()"
      ("math" is a standard built-in module). The number and type of
      the arguments are determined by the C function. Special read-
      only attributes: "__doc__" is the function's documentation
      string, or "None" if unavailable; "__name__" is the function's
      name; "__self__" is set to "None" (but see the next item);
      "__module__" is the name of the module the function was defined
      in or "None" if unavailable.

   Built-in methods
      This is really a different disguise of a built-in function, this
      time containing an object passed to the C function as an
      implicit extra argument.  An example of a built-in method is
      "alist.append()", assuming *alist* is a list object. In this
      case, the special read-only attribute "__self__" is set to the
      object denoted by *alist*.

   Classes
      Classes are callable.  These objects normally act as factories
      for new instances of themselves, but variations are possible for
      class types that override "__new__()".  The arguments of the
      call are passed to "__new__()" and, in the typical case, to
      "__init__()" to initialize the new instance.

   Class Instances
      Instances of arbitrary classes can be made callable by defining
      a "__call__()" method in their class.

Modules
   Modules are a basic organizational unit of Python code, and are
   created by the import system as invoked either by the "import"
   statement (see "import"), or by calling functions such as
   "importlib.import_module()" and built-in "__import__()".  A module
   object has a namespace implemented by a dictionary object (this is
   the dictionary referenced by the "__globals__" attribute of
   functions defined in the module).  Attribute references are
   translated to lookups in this dictionary, e.g., "m.x" is equivalent
   to "m.__dict__["x"]". A module object does not contain the code
   object used to initialize the module (since it isn't needed once
   the initialization is done).

   Attribute assignment updates the module's namespace dictionary,
   e.g., "m.x = 1" is equivalent to "m.__dict__["x"] = 1".

   Predefined (writable) attributes: "__name__" is the module's name;
   "__doc__" is the module's documentation string, or "None" if
   unavailable; "__annotations__" (optional) is a dictionary
   containing *variable annotations* collected during module body
   execution; "__file__" is the pathname of the file from which the
   module was loaded, if it was loaded from a file. The "__file__"
   attribute may be missing for certain types of modules, such as C
   modules that are statically linked into the interpreter; for
   extension modules loaded dynamically from a shared library, it is
   the pathname of the shared library file.

   Special read-only attribute: "__dict__" is the module's namespace
   as a dictionary object.

   **CPython implementation detail:** Because of the way CPython
   clears module dictionaries, the module dictionary will be cleared
   when the module falls out of scope even if the dictionary still has
   live references.  To avoid this, copy the dictionary or keep the
   module around while using its dictionary directly.

Custom classes
   Custom class types are typically created by class definitions (see
   section Class definitions).  A class has a namespace implemented by
   a dictionary object. Class attribute references are translated to
   lookups in this dictionary, e.g., "C.x" is translated to
   "C.__dict__["x"]" (although there are a number of hooks which allow
   for other means of locating attributes). When the attribute name is
   not found there, the attribute search continues in the base
   classes. This search of the base classes uses the C3 method
   resolution order which behaves correctly even in the presence of
   'diamond' inheritance structures where there are multiple
   inheritance paths leading back to a common ancestor. Additional
   details on the C3 MRO used by Python can be found in the
   documentation accompanying the 2.3 release at
   https://www.python.org/download/releases/2.3/mro/.

   When a class attribute reference (for class "C", say) would yield a
   class method object, it is transformed into an instance method
   object whose "__self__" attributes is "C".  When it would yield a
   static method object, it is transformed into the object wrapped by
   the static method object. See section Implementing Descriptors for
   another way in which attributes retrieved from a class may differ
   from those actually contained in its "__dict__".

   Class attribute assignments update the class's dictionary, never
   the dictionary of a base class.

   A class object can be called (see above) to yield a class instance
   (see below).

   Special attributes: "__name__" is the class name; "__module__" is
   the module name in which the class was defined; "__dict__" is the
   dictionary containing the class's namespace; "__bases__" is a tuple
   containing the base classes, in the order of their occurrence in
   the base class list; "__doc__" is the class's documentation string,
   or "None" if undefined; "__annotations__" (optional) is a
   dictionary containing *variable annotations* collected during class
   body execution.

Class instances
   A class instance is created by calling a class object (see above).
   A class instance has a namespace implemented as a dictionary which
   is the first place in which attribute references are searched.
   When an attribute is not found there, and the instance's class has
   an attribute by that name, the search continues with the class
   attributes.  If a class attribute is found that is a user-defined
   function object, it is transformed into an instance method object
   whose "__self__" attribute is the instance.  Static method and
   class method objects are also transformed; see above under
   "Classes".  See section Implementing Descriptors for another way in
   which attributes of a class retrieved via its instances may differ
   from the objects actually stored in the class's "__dict__".  If no
   class attribute is found, and the object's class has a
   "__getattr__()" method, that is called to satisfy the lookup.

   Attribute assignments and deletions update the instance's
   dictionary, never a class's dictionary.  If the class has a
   "__setattr__()" or "__delattr__()" method, this is called instead
   of updating the instance dictionary directly.

   Class instances can pretend to be numbers, sequences, or mappings
   if they have methods with certain special names.  See section
   Special method names.

   Special attributes: "__dict__" is the attribute dictionary;
   "__class__" is the instance's class.

I/O objects (also known as file objects)
   A *file object* represents an open file.  Various shortcuts are
   available to create file objects: the "open()" built-in function,
   and also "os.popen()", "os.fdopen()", and the "makefile()" method
   of socket objects (and perhaps by other functions or methods
   provided by extension modules).

   The objects "sys.stdin", "sys.stdout" and "sys.stderr" are
   initialized to file objects corresponding to the interpreter's
   standard input, output and error streams; they are all open in text
   mode and therefore follow the interface defined by the
   "io.TextIOBase" abstract class.

Internal types
   A few types used internally by the interpreter are exposed to the
   user. Their definitions may change with future versions of the
   interpreter, but they are mentioned here for completeness.

   Code objects
      Code objects represent *byte-compiled* executable Python code,
      or *bytecode*. The difference between a code object and a
      function object is that the function object contains an explicit
      reference to the function's globals (the module in which it was
      defined), while a code object contains no context; also the
      default argument values are stored in the function object, not
      in the code object (because they represent values calculated at
      run-time).  Unlike function objects, code objects are immutable
      and contain no references (directly or indirectly) to mutable
      objects.

      Special read-only attributes: "co_name" gives the function name;
      "co_argcount" is the number of positional arguments (including
      arguments with default values); "co_nlocals" is the number of
      local variables used by the function (including arguments);
      "co_varnames" is a tuple containing the names of the local
      variables (starting with the argument names); "co_cellvars" is a
      tuple containing the names of local variables that are
      referenced by nested functions; "co_freevars" is a tuple
      containing the names of free variables; "co_code" is a string
      representing the sequence of bytecode instructions; "co_consts"
      is a tuple containing the literals used by the bytecode;
      "co_names" is a tuple containing the names used by the bytecode;
      "co_filename" is the filename from which the code was compiled;
      "co_firstlineno" is the first line number of the function;
      "co_lnotab" is a string encoding the mapping from bytecode
      offsets to line numbers (for details see the source code of the
      interpreter); "co_stacksize" is the required stack size
      (including local variables); "co_flags" is an integer encoding a
      number of flags for the interpreter.

      The following flag bits are defined for "co_flags": bit "0x04"
      is set if the function uses the "*arguments" syntax to accept an
      arbitrary number of positional arguments; bit "0x08" is set if
      the function uses the "**keywords" syntax to accept arbitrary
      keyword arguments; bit "0x20" is set if the function is a
      generator.

      Future feature declarations ("from __future__ import division")
      also use bits in "co_flags" to indicate whether a code object
      was compiled with a particular feature enabled: bit "0x2000" is
      set if the function was compiled with future division enabled;
      bits "0x10" and "0x1000" were used in earlier versions of
      Python.

      Other bits in "co_flags" are reserved for internal use.

      If a code object represents a function, the first item in
      "co_consts" is the documentation string of the function, or
      "None" if undefined.

   Frame objects
      Frame objects represent execution frames.  They may occur in
      traceback objects (see below).

      Special read-only attributes: "f_back" is to the previous stack
      frame (towards the caller), or "None" if this is the bottom
      stack frame; "f_code" is the code object being executed in this
      frame; "f_locals" is the dictionary used to look up local
      variables; "f_globals" is used for global variables;
      "f_builtins" is used for built-in (intrinsic) names; "f_lasti"
      gives the precise instruction (this is an index into the
      bytecode string of the code object).

      Special writable attributes: "f_trace", if not "None", is a
      function called at the start of each source code line (this is
      used by the debugger); "f_lineno" is the current line number of
      the frame --- writing to this from within a trace function jumps
      to the given line (only for the bottom-most frame).  A debugger
      can implement a Jump command (aka Set Next Statement) by writing
      to f_lineno.

      Frame objects support one method:

      frame.clear()

         This method clears all references to local variables held by
         the frame.  Also, if the frame belonged to a generator, the
         generator is finalized.  This helps break reference cycles
         involving frame objects (for example when catching an
         exception and storing its traceback for later use).

         "RuntimeError" is raised if the frame is currently executing.

         New in version 3.4.

   Traceback objects
      Traceback objects represent a stack trace of an exception.  A
      traceback object is created when an exception occurs.  When the
      search for an exception handler unwinds the execution stack, at
      each unwound level a traceback object is inserted in front of
      the current traceback.  When an exception handler is entered,
      the stack trace is made available to the program. (See section
      The try statement.) It is accessible as the third item of the
      tuple returned by "sys.exc_info()". When the program contains no
      suitable handler, the stack trace is written (nicely formatted)
      to the standard error stream; if the interpreter is interactive,
      it is also made available to the user as "sys.last_traceback".

      Special read-only attributes: "tb_next" is the next level in the
      stack trace (towards the frame where the exception occurred), or
      "None" if there is no next level; "tb_frame" points to the
      execution frame of the current level; "tb_lineno" gives the line
      number where the exception occurred; "tb_lasti" indicates the
      precise instruction.  The line number and last instruction in
      the traceback may differ from the line number of its frame
      object if the exception occurred in a "try" statement with no
      matching except clause or with a finally clause.

   Slice objects
      Slice objects are used to represent slices for "__getitem__()"
      methods.  They are also created by the built-in "slice()"
      function.

      Special read-only attributes: "start" is the lower bound; "stop"
      is the upper bound; "step" is the step value; each is "None" if
      omitted.  These attributes can have any type.

      Slice objects support one method:

      slice.indices(self, length)

         This method takes a single integer argument *length* and
         computes information about the slice that the slice object
         would describe if applied to a sequence of *length* items.
         It returns a tuple of three integers; respectively these are
         the *start* and *stop* indices and the *step* or stride
         length of the slice. Missing or out-of-bounds indices are
         handled in a manner consistent with regular slices.

   Static method objects
      Static method objects provide a way of defeating the
      transformation of function objects to method objects described
      above. A static method object is a wrapper around any other
      object, usually a user-defined method object. When a static
      method object is retrieved from a class or a class instance, the
      object actually returned is the wrapped object, which is not
      subject to any further transformation. Static method objects are
      not themselves callable, although the objects they wrap usually
      are. Static method objects are created by the built-in
      "staticmethod()" constructor.

   Class method objects
      A class method object, like a static method object, is a wrapper
      around another object that alters the way in which that object
      is retrieved from classes and class instances. The behaviour of
      class method objects upon such retrieval is described above,
      under "User-defined methods". Class method objects are created
      by the built-in "classmethod()" constructor.
"""
    , 'typesfunctions':
    """Functions
*********

Function objects are created by function definitions.  The only
operation on a function object is to call it: "func(argument-list)".

There are really two flavors of function objects: built-in functions
and user-defined functions.  Both support the same operation (to call
the function), but the implementation is different, hence the
different object types.

See Function definitions for more information.
"""
    , 'typesmapping':
    """Mapping Types --- "dict"
************************

A *mapping* object maps *hashable* values to arbitrary objects.
Mappings are mutable objects.  There is currently only one standard
mapping type, the *dictionary*.  (For other containers see the built-
in "list", "set", and "tuple" classes, and the "collections" module.)

A dictionary's keys are *almost* arbitrary values.  Values that are
not *hashable*, that is, values containing lists, dictionaries or
other mutable types (that are compared by value rather than by object
identity) may not be used as keys.  Numeric types used for keys obey
the normal rules for numeric comparison: if two numbers compare equal
(such as "1" and "1.0") then they can be used interchangeably to index
the same dictionary entry.  (Note however, that since computers store
floating-point numbers as approximations it is usually unwise to use
them as dictionary keys.)

Dictionaries can be created by placing a comma-separated list of "key:
value" pairs within braces, for example: "{'jack': 4098, 'sjoerd':
4127}" or "{4098: 'jack', 4127: 'sjoerd'}", or by the "dict"
constructor.

class dict(**kwarg)
class dict(mapping, **kwarg)
class dict(iterable, **kwarg)

   Return a new dictionary initialized from an optional positional
   argument and a possibly empty set of keyword arguments.

   If no positional argument is given, an empty dictionary is created.
   If a positional argument is given and it is a mapping object, a
   dictionary is created with the same key-value pairs as the mapping
   object.  Otherwise, the positional argument must be an *iterable*
   object.  Each item in the iterable must itself be an iterable with
   exactly two objects.  The first object of each item becomes a key
   in the new dictionary, and the second object the corresponding
   value.  If a key occurs more than once, the last value for that key
   becomes the corresponding value in the new dictionary.

   If keyword arguments are given, the keyword arguments and their
   values are added to the dictionary created from the positional
   argument.  If a key being added is already present, the value from
   the keyword argument replaces the value from the positional
   argument.

   To illustrate, the following examples all return a dictionary equal
   to "{"one": 1, "two": 2, "three": 3}":

      >>> a = dict(one=1, two=2, three=3)
      >>> b = {'one': 1, 'two': 2, 'three': 3}
      >>> c = dict(zip(['one', 'two', 'three'], [1, 2, 3]))
      >>> d = dict([('two', 2), ('one', 1), ('three', 3)])
      >>> e = dict({'three': 3, 'one': 1, 'two': 2})
      >>> a == b == c == d == e
      True

   Providing keyword arguments as in the first example only works for
   keys that are valid Python identifiers.  Otherwise, any valid keys
   can be used.

   These are the operations that dictionaries support (and therefore,
   custom mapping types should support too):

   len(d)

      Return the number of items in the dictionary *d*.

   d[key]

      Return the item of *d* with key *key*.  Raises a "KeyError" if
      *key* is not in the map.

      If a subclass of dict defines a method "__missing__()" and *key*
      is not present, the "d[key]" operation calls that method with
      the key *key* as argument.  The "d[key]" operation then returns
      or raises whatever is returned or raised by the
      "__missing__(key)" call. No other operations or methods invoke
      "__missing__()". If "__missing__()" is not defined, "KeyError"
      is raised. "__missing__()" must be a method; it cannot be an
      instance variable:

         >>> class Counter(dict):
         ...     def __missing__(self, key):
         ...         return 0
         >>> c = Counter()
         >>> c['red']
         0
         >>> c['red'] += 1
         >>> c['red']
         1

      The example above shows part of the implementation of
      "collections.Counter".  A different "__missing__" method is used
      by "collections.defaultdict".

   d[key] = value

      Set "d[key]" to *value*.

   del d[key]

      Remove "d[key]" from *d*.  Raises a "KeyError" if *key* is not
      in the map.

   key in d

      Return "True" if *d* has a key *key*, else "False".

   key not in d

      Equivalent to "not key in d".

   iter(d)

      Return an iterator over the keys of the dictionary.  This is a
      shortcut for "iter(d.keys())".

   clear()

      Remove all items from the dictionary.

   copy()

      Return a shallow copy of the dictionary.

   classmethod fromkeys(seq[, value])

      Create a new dictionary with keys from *seq* and values set to
      *value*.

      "fromkeys()" is a class method that returns a new dictionary.
      *value* defaults to "None".

   get(key[, default])

      Return the value for *key* if *key* is in the dictionary, else
      *default*. If *default* is not given, it defaults to "None", so
      that this method never raises a "KeyError".

   items()

      Return a new view of the dictionary's items ("(key, value)"
      pairs). See the documentation of view objects.

   keys()

      Return a new view of the dictionary's keys.  See the
      documentation of view objects.

   pop(key[, default])

      If *key* is in the dictionary, remove it and return its value,
      else return *default*.  If *default* is not given and *key* is
      not in the dictionary, a "KeyError" is raised.

   popitem()

      Remove and return an arbitrary "(key, value)" pair from the
      dictionary.

      "popitem()" is useful to destructively iterate over a
      dictionary, as often used in set algorithms.  If the dictionary
      is empty, calling "popitem()" raises a "KeyError".

   setdefault(key[, default])

      If *key* is in the dictionary, return its value.  If not, insert
      *key* with a value of *default* and return *default*.  *default*
      defaults to "None".

   update([other])

      Update the dictionary with the key/value pairs from *other*,
      overwriting existing keys.  Return "None".

      "update()" accepts either another dictionary object or an
      iterable of key/value pairs (as tuples or other iterables of
      length two).  If keyword arguments are specified, the dictionary
      is then updated with those key/value pairs: "d.update(red=1,
      blue=2)".

   values()

      Return a new view of the dictionary's values.  See the
      documentation of view objects.

   Dictionaries compare equal if and only if they have the same "(key,
   value)" pairs. Order comparisons ('<', '<=', '>=', '>') raise
   "TypeError".

See also: "types.MappingProxyType" can be used to create a read-only
  view of a "dict".


Dictionary view objects
=======================

The objects returned by "dict.keys()", "dict.values()" and
"dict.items()" are *view objects*.  They provide a dynamic view on the
dictionary's entries, which means that when the dictionary changes,
the view reflects these changes.

Dictionary views can be iterated over to yield their respective data,
and support membership tests:

len(dictview)

   Return the number of entries in the dictionary.

iter(dictview)

   Return an iterator over the keys, values or items (represented as
   tuples of "(key, value)") in the dictionary.

   Keys and values are iterated over in an arbitrary order which is
   non-random, varies across Python implementations, and depends on
   the dictionary's history of insertions and deletions. If keys,
   values and items views are iterated over with no intervening
   modifications to the dictionary, the order of items will directly
   correspond.  This allows the creation of "(value, key)" pairs using
   "zip()": "pairs = zip(d.values(), d.keys())".  Another way to
   create the same list is "pairs = [(v, k) for (k, v) in d.items()]".

   Iterating views while adding or deleting entries in the dictionary
   may raise a "RuntimeError" or fail to iterate over all entries.

x in dictview

   Return "True" if *x* is in the underlying dictionary's keys, values
   or items (in the latter case, *x* should be a "(key, value)"
   tuple).

Keys views are set-like since their entries are unique and hashable.
If all values are hashable, so that "(key, value)" pairs are unique
and hashable, then the items view is also set-like.  (Values views are
not treated as set-like since the entries are generally not unique.)
For set-like views, all of the operations defined for the abstract
base class "collections.abc.Set" are available (for example, "==",
"<", or "^").

An example of dictionary view usage:

   >>> dishes = {'eggs': 2, 'sausage': 1, 'bacon': 1, 'spam': 500}
   >>> keys = dishes.keys()
   >>> values = dishes.values()

   >>> # iteration
   >>> n = 0
   >>> for val in values:
   ...     n += val
   >>> print(n)
   504

   >>> # keys and values are iterated over in the same order
   >>> list(keys)
   ['eggs', 'bacon', 'sausage', 'spam']
   >>> list(values)
   [2, 1, 1, 500]

   >>> # view objects are dynamic and reflect dict changes
   >>> del dishes['eggs']
   >>> del dishes['sausage']
   >>> list(keys)
   ['spam', 'bacon']

   >>> # set operations
   >>> keys & {'eggs', 'bacon', 'salad'}
   {'bacon'}
   >>> keys ^ {'sausage', 'juice'}
   {'juice', 'sausage', 'bacon', 'spam'}
"""
    , 'typesmethods':
    """Methods
*******

Methods are functions that are called using the attribute notation.
There are two flavors: built-in methods (such as "append()" on lists)
and class instance methods.  Built-in methods are described with the
types that support them.

If you access a method (a function defined in a class namespace)
through an instance, you get a special object: a *bound method* (also
called *instance method*) object. When called, it will add the "self"
argument to the argument list.  Bound methods have two special read-
only attributes: "m.__self__" is the object on which the method
operates, and "m.__func__" is the function implementing the method.
Calling "m(arg-1, arg-2, ..., arg-n)" is completely equivalent to
calling "m.__func__(m.__self__, arg-1, arg-2, ..., arg-n)".

Like function objects, bound method objects support getting arbitrary
attributes.  However, since method attributes are actually stored on
the underlying function object ("meth.__func__"), setting method
attributes on bound methods is disallowed.  Attempting to set an
attribute on a method results in an "AttributeError" being raised.  In
order to set a method attribute, you need to explicitly set it on the
underlying function object:

   >>> class C:
   ...     def method(self):
   ...         pass
   ...
   >>> c = C()
   >>> c.method.whoami = 'my name is method'  # can't set on the method
   Traceback (most recent call last):
     File "<stdin>", line 1, in <module>
   AttributeError: 'method' object has no attribute 'whoami'
   >>> c.method.__func__.whoami = 'my name is method'
   >>> c.method.whoami
   'my name is method'

See The standard type hierarchy for more information.
"""
    , 'typesmodules':
    """Modules
*******

The only special operation on a module is attribute access: "m.name",
where *m* is a module and *name* accesses a name defined in *m*'s
symbol table. Module attributes can be assigned to.  (Note that the
"import" statement is not, strictly speaking, an operation on a module
object; "import foo" does not require a module object named *foo* to
exist, rather it requires an (external) *definition* for a module
named *foo* somewhere.)

A special attribute of every module is "__dict__". This is the
dictionary containing the module's symbol table. Modifying this
dictionary will actually change the module's symbol table, but direct
assignment to the "__dict__" attribute is not possible (you can write
"m.__dict__['a'] = 1", which defines "m.a" to be "1", but you can't
write "m.__dict__ = {}").  Modifying "__dict__" directly is not
recommended.

Modules built into the interpreter are written like this: "<module
'sys' (built-in)>".  If loaded from a file, they are written as
"<module 'os' from '/usr/local/lib/pythonX.Y/os.pyc'>".
"""
    , 'typesseq':
    """Sequence Types --- "list", "tuple", "range"
*******************************************

There are three basic sequence types: lists, tuples, and range
objects. Additional sequence types tailored for processing of binary
data and text strings are described in dedicated sections.


Common Sequence Operations
==========================

The operations in the following table are supported by most sequence
types, both mutable and immutable. The "collections.abc.Sequence" ABC
is provided to make it easier to correctly implement these operations
on custom sequence types.

This table lists the sequence operations sorted in ascending priority.
In the table, *s* and *t* are sequences of the same type, *n*, *i*,
*j* and *k* are integers and *x* is an arbitrary object that meets any
type and value restrictions imposed by *s*.

The "in" and "not in" operations have the same priorities as the
comparison operations. The "+" (concatenation) and "*" (repetition)
operations have the same priority as the corresponding numeric
operations. [3]

+----------------------------+----------------------------------+------------+
| Operation                  | Result                           | Notes      |
+============================+==================================+============+
| "x in s"                   | "True" if an item of *s* is      | (1)        |
|                            | equal to *x*, else "False"       |            |
+----------------------------+----------------------------------+------------+
| "x not in s"               | "False" if an item of *s* is     | (1)        |
|                            | equal to *x*, else "True"        |            |
+----------------------------+----------------------------------+------------+
| "s + t"                    | the concatenation of *s* and *t* | (6)(7)     |
+----------------------------+----------------------------------+------------+
| "s * n" or "n * s"         | equivalent to adding *s* to      | (2)(7)     |
|                            | itself *n* times                 |            |
+----------------------------+----------------------------------+------------+
| "s[i]"                     | *i*th item of *s*, origin 0      | (3)        |
+----------------------------+----------------------------------+------------+
| "s[i:j]"                   | slice of *s* from *i* to *j*     | (3)(4)     |
+----------------------------+----------------------------------+------------+
| "s[i:j:k]"                 | slice of *s* from *i* to *j*     | (3)(5)     |
|                            | with step *k*                    |            |
+----------------------------+----------------------------------+------------+
| "len(s)"                   | length of *s*                    |            |
+----------------------------+----------------------------------+------------+
| "min(s)"                   | smallest item of *s*             |            |
+----------------------------+----------------------------------+------------+
| "max(s)"                   | largest item of *s*              |            |
+----------------------------+----------------------------------+------------+
| "s.index(x[, i[, j]])"     | index of the first occurrence of | (8)        |
|                            | *x* in *s* (at or after index    |            |
|                            | *i* and before index *j*)        |            |
+----------------------------+----------------------------------+------------+
| "s.count(x)"               | total number of occurrences of   |            |
|                            | *x* in *s*                       |            |
+----------------------------+----------------------------------+------------+

Sequences of the same type also support comparisons.  In particular,
tuples and lists are compared lexicographically by comparing
corresponding elements. This means that to compare equal, every
element must compare equal and the two sequences must be of the same
type and have the same length.  (For full details see Comparisons in
the language reference.)

Notes:

1. While the "in" and "not in" operations are used only for simple
   containment testing in the general case, some specialised sequences
   (such as "str", "bytes" and "bytearray") also use them for
   subsequence testing:

      >>> "gg" in "eggs"
      True

2. Values of *n* less than "0" are treated as "0" (which yields an
   empty sequence of the same type as *s*).  Note that items in the
   sequence *s* are not copied; they are referenced multiple times.
   This often haunts new Python programmers; consider:

      >>> lists = [[]] * 3
      >>> lists
      [[], [], []]
      >>> lists[0].append(3)
      >>> lists
      [[3], [3], [3]]

   What has happened is that "[[]]" is a one-element list containing
   an empty list, so all three elements of "[[]] * 3" are references
   to this single empty list.  Modifying any of the elements of
   "lists" modifies this single list. You can create a list of
   different lists this way:

      >>> lists = [[] for i in range(3)]
      >>> lists[0].append(3)
      >>> lists[1].append(5)
      >>> lists[2].append(7)
      >>> lists
      [[3], [5], [7]]

   Further explanation is available in the FAQ entry How do I create a
   multidimensional list?.

3. If *i* or *j* is negative, the index is relative to the end of
   sequence *s*: "len(s) + i" or "len(s) + j" is substituted.  But
   note that "-0" is still "0".

4. The slice of *s* from *i* to *j* is defined as the sequence of
   items with index *k* such that "i <= k < j".  If *i* or *j* is
   greater than "len(s)", use "len(s)".  If *i* is omitted or "None",
   use "0".  If *j* is omitted or "None", use "len(s)".  If *i* is
   greater than or equal to *j*, the slice is empty.

5. The slice of *s* from *i* to *j* with step *k* is defined as the
   sequence of items with index  "x = i + n*k" such that "0 <= n <
   (j-i)/k".  In other words, the indices are "i", "i+k", "i+2*k",
   "i+3*k" and so on, stopping when *j* is reached (but never
   including *j*).  When *k* is positive, *i* and *j* are reduced to
   "len(s)" if they are greater. When *k* is negative, *i* and *j* are
   reduced to "len(s) - 1" if they are greater.  If *i* or *j* are
   omitted or "None", they become "end" values (which end depends on
   the sign of *k*).  Note, *k* cannot be zero. If *k* is "None", it
   is treated like "1".

6. Concatenating immutable sequences always results in a new
   object. This means that building up a sequence by repeated
   concatenation will have a quadratic runtime cost in the total
   sequence length. To get a linear runtime cost, you must switch to
   one of the alternatives below:

   * if concatenating "str" objects, you can build a list and use
     "str.join()" at the end or else write to an "io.StringIO"
     instance and retrieve its value when complete

   * if concatenating "bytes" objects, you can similarly use
     "bytes.join()" or "io.BytesIO", or you can do in-place
     concatenation with a "bytearray" object.  "bytearray" objects are
     mutable and have an efficient overallocation mechanism

   * if concatenating "tuple" objects, extend a "list" instead

   * for other types, investigate the relevant class documentation

7. Some sequence types (such as "range") only support item
   sequences that follow specific patterns, and hence don't support
   sequence concatenation or repetition.

8. "index" raises "ValueError" when *x* is not found in *s*. When
   supported, the additional arguments to the index method allow
   efficient searching of subsections of the sequence. Passing the
   extra arguments is roughly equivalent to using "s[i:j].index(x)",
   only without copying any data and with the returned index being
   relative to the start of the sequence rather than the start of the
   slice.


Immutable Sequence Types
========================

The only operation that immutable sequence types generally implement
that is not also implemented by mutable sequence types is support for
the "hash()" built-in.

This support allows immutable sequences, such as "tuple" instances, to
be used as "dict" keys and stored in "set" and "frozenset" instances.

Attempting to hash an immutable sequence that contains unhashable
values will result in "TypeError".


Mutable Sequence Types
======================

The operations in the following table are defined on mutable sequence
types. The "collections.abc.MutableSequence" ABC is provided to make
it easier to correctly implement these operations on custom sequence
types.

In the table *s* is an instance of a mutable sequence type, *t* is any
iterable object and *x* is an arbitrary object that meets any type and
value restrictions imposed by *s* (for example, "bytearray" only
accepts integers that meet the value restriction "0 <= x <= 255").

+--------------------------------+----------------------------------+-----------------------+
| Operation                      | Result                           | Notes                 |
+================================+==================================+=======================+
| "s[i] = x"                     | item *i* of *s* is replaced by   |                       |
|                                | *x*                              |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s[i:j] = t"                   | slice of *s* from *i* to *j* is  |                       |
|                                | replaced by the contents of the  |                       |
|                                | iterable *t*                     |                       |
+--------------------------------+----------------------------------+-----------------------+
| "del s[i:j]"                   | same as "s[i:j] = []"            |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s[i:j:k] = t"                 | the elements of "s[i:j:k]" are   | (1)                   |
|                                | replaced by those of *t*         |                       |
+--------------------------------+----------------------------------+-----------------------+
| "del s[i:j:k]"                 | removes the elements of          |                       |
|                                | "s[i:j:k]" from the list         |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.append(x)"                  | appends *x* to the end of the    |                       |
|                                | sequence (same as                |                       |
|                                | "s[len(s):len(s)] = [x]")        |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.clear()"                    | removes all items from "s" (same | (5)                   |
|                                | as "del s[:]")                   |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.copy()"                     | creates a shallow copy of "s"    | (5)                   |
|                                | (same as "s[:]")                 |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.extend(t)" or "s += t"      | extends *s* with the contents of |                       |
|                                | *t* (for the most part the same  |                       |
|                                | as "s[len(s):len(s)] = t")       |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s *= n"                       | updates *s* with its contents    | (6)                   |
|                                | repeated *n* times               |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.insert(i, x)"               | inserts *x* into *s* at the      |                       |
|                                | index given by *i* (same as      |                       |
|                                | "s[i:i] = [x]")                  |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.pop([i])"                   | retrieves the item at *i* and    | (2)                   |
|                                | also removes it from *s*         |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.remove(x)"                  | remove the first item from *s*   | (3)                   |
|                                | where "s[i] == x"                |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.reverse()"                  | reverses the items of *s* in     | (4)                   |
|                                | place                            |                       |
+--------------------------------+----------------------------------+-----------------------+

Notes:

1. *t* must have the same length as the slice it is replacing.

2. The optional argument *i* defaults to "-1", so that by default
   the last item is removed and returned.

3. "remove" raises "ValueError" when *x* is not found in *s*.

4. The "reverse()" method modifies the sequence in place for
   economy of space when reversing a large sequence.  To remind users
   that it operates by side effect, it does not return the reversed
   sequence.

5. "clear()" and "copy()" are included for consistency with the
   interfaces of mutable containers that don't support slicing
   operations (such as "dict" and "set")

   New in version 3.3: "clear()" and "copy()" methods.

6. The value *n* is an integer, or an object implementing
   "__index__()".  Zero and negative values of *n* clear the sequence.
   Items in the sequence are not copied; they are referenced multiple
   times, as explained for "s * n" under Common Sequence Operations.


Lists
=====

Lists are mutable sequences, typically used to store collections of
homogeneous items (where the precise degree of similarity will vary by
application).

class list([iterable])

   Lists may be constructed in several ways:

   * Using a pair of square brackets to denote the empty list: "[]"

   * Using square brackets, separating items with commas: "[a]",
     "[a, b, c]"

   * Using a list comprehension: "[x for x in iterable]"

   * Using the type constructor: "list()" or "list(iterable)"

   The constructor builds a list whose items are the same and in the
   same order as *iterable*'s items.  *iterable* may be either a
   sequence, a container that supports iteration, or an iterator
   object.  If *iterable* is already a list, a copy is made and
   returned, similar to "iterable[:]". For example, "list('abc')"
   returns "['a', 'b', 'c']" and "list( (1, 2, 3) )" returns "[1, 2,
   3]". If no argument is given, the constructor creates a new empty
   list, "[]".

   Many other operations also produce lists, including the "sorted()"
   built-in.

   Lists implement all of the common and mutable sequence operations.
   Lists also provide the following additional method:

   sort(*, key=None, reverse=None)

      This method sorts the list in place, using only "<" comparisons
      between items. Exceptions are not suppressed - if any comparison
      operations fail, the entire sort operation will fail (and the
      list will likely be left in a partially modified state).

      "sort()" accepts two arguments that can only be passed by
      keyword (keyword-only arguments):

      *key* specifies a function of one argument that is used to
      extract a comparison key from each list element (for example,
      "key=str.lower"). The key corresponding to each item in the list
      is calculated once and then used for the entire sorting process.
      The default value of "None" means that list items are sorted
      directly without calculating a separate key value.

      The "functools.cmp_to_key()" utility is available to convert a
      2.x style *cmp* function to a *key* function.

      *reverse* is a boolean value.  If set to "True", then the list
      elements are sorted as if each comparison were reversed.

      This method modifies the sequence in place for economy of space
      when sorting a large sequence.  To remind users that it operates
      by side effect, it does not return the sorted sequence (use
      "sorted()" to explicitly request a new sorted list instance).

      The "sort()" method is guaranteed to be stable.  A sort is
      stable if it guarantees not to change the relative order of
      elements that compare equal --- this is helpful for sorting in
      multiple passes (for example, sort by department, then by salary
      grade).

      **CPython implementation detail:** While a list is being sorted,
      the effect of attempting to mutate, or even inspect, the list is
      undefined.  The C implementation of Python makes the list appear
      empty for the duration, and raises "ValueError" if it can detect
      that the list has been mutated during a sort.


Tuples
======

Tuples are immutable sequences, typically used to store collections of
heterogeneous data (such as the 2-tuples produced by the "enumerate()"
built-in). Tuples are also used for cases where an immutable sequence
of homogeneous data is needed (such as allowing storage in a "set" or
"dict" instance).

class tuple([iterable])

   Tuples may be constructed in a number of ways:

   * Using a pair of parentheses to denote the empty tuple: "()"

   * Using a trailing comma for a singleton tuple: "a," or "(a,)"

   * Separating items with commas: "a, b, c" or "(a, b, c)"

   * Using the "tuple()" built-in: "tuple()" or "tuple(iterable)"

   The constructor builds a tuple whose items are the same and in the
   same order as *iterable*'s items.  *iterable* may be either a
   sequence, a container that supports iteration, or an iterator
   object.  If *iterable* is already a tuple, it is returned
   unchanged. For example, "tuple('abc')" returns "('a', 'b', 'c')"
   and "tuple( [1, 2, 3] )" returns "(1, 2, 3)". If no argument is
   given, the constructor creates a new empty tuple, "()".

   Note that it is actually the comma which makes a tuple, not the
   parentheses. The parentheses are optional, except in the empty
   tuple case, or when they are needed to avoid syntactic ambiguity.
   For example, "f(a, b, c)" is a function call with three arguments,
   while "f((a, b, c))" is a function call with a 3-tuple as the sole
   argument.

   Tuples implement all of the common sequence operations.

For heterogeneous collections of data where access by name is clearer
than access by index, "collections.namedtuple()" may be a more
appropriate choice than a simple tuple object.


Ranges
======

The "range" type represents an immutable sequence of numbers and is
commonly used for looping a specific number of times in "for" loops.

class range(stop)
class range(start, stop[, step])

   The arguments to the range constructor must be integers (either
   built-in "int" or any object that implements the "__index__"
   special method).  If the *step* argument is omitted, it defaults to
   "1". If the *start* argument is omitted, it defaults to "0". If
   *step* is zero, "ValueError" is raised.

   For a positive *step*, the contents of a range "r" are determined
   by the formula "r[i] = start + step*i" where "i >= 0" and "r[i] <
   stop".

   For a negative *step*, the contents of the range are still
   determined by the formula "r[i] = start + step*i", but the
   constraints are "i >= 0" and "r[i] > stop".

   A range object will be empty if "r[0]" does not meet the value
   constraint. Ranges do support negative indices, but these are
   interpreted as indexing from the end of the sequence determined by
   the positive indices.

   Ranges containing absolute values larger than "sys.maxsize" are
   permitted but some features (such as "len()") may raise
   "OverflowError".

   Range examples:

      >>> list(range(10))
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
      >>> list(range(1, 11))
      [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
      >>> list(range(0, 30, 5))
      [0, 5, 10, 15, 20, 25]
      >>> list(range(0, 10, 3))
      [0, 3, 6, 9]
      >>> list(range(0, -10, -1))
      [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]
      >>> list(range(0))
      []
      >>> list(range(1, 0))
      []

   Ranges implement all of the common sequence operations except
   concatenation and repetition (due to the fact that range objects
   can only represent sequences that follow a strict pattern and
   repetition and concatenation will usually violate that pattern).

   start

      The value of the *start* parameter (or "0" if the parameter was
      not supplied)

   stop

      The value of the *stop* parameter

   step

      The value of the *step* parameter (or "1" if the parameter was
      not supplied)

The advantage of the "range" type over a regular "list" or "tuple" is
that a "range" object will always take the same (small) amount of
memory, no matter the size of the range it represents (as it only
stores the "start", "stop" and "step" values, calculating individual
items and subranges as needed).

Range objects implement the "collections.abc.Sequence" ABC, and
provide features such as containment tests, element index lookup,
slicing and support for negative indices (see Sequence Types --- list,
tuple, range):

>>> r = range(0, 20, 2)
>>> r
range(0, 20, 2)
>>> 11 in r
False
>>> 10 in r
True
>>> r.index(10)
5
>>> r[5]
10
>>> r[:5]
range(0, 10, 2)
>>> r[-1]
18

Testing range objects for equality with "==" and "!=" compares them as
sequences.  That is, two range objects are considered equal if they
represent the same sequence of values.  (Note that two range objects
that compare equal might have different "start", "stop" and "step"
attributes, for example "range(0) == range(2, 1, 3)" or "range(0, 3,
2) == range(0, 4, 2)".)

Changed in version 3.2: Implement the Sequence ABC. Support slicing
and negative indices. Test "int" objects for membership in constant
time instead of iterating through all items.

Changed in version 3.3: Define '==' and '!=' to compare range objects
based on the sequence of values they define (instead of comparing
based on object identity).

New in version 3.3: The "start", "stop" and "step" attributes.

See also:

  * The linspace recipe shows how to implement a lazy version of
    range that suitable for floating point applications.
"""
    , 'typesseq-mutable':
    """Mutable Sequence Types
**********************

The operations in the following table are defined on mutable sequence
types. The "collections.abc.MutableSequence" ABC is provided to make
it easier to correctly implement these operations on custom sequence
types.

In the table *s* is an instance of a mutable sequence type, *t* is any
iterable object and *x* is an arbitrary object that meets any type and
value restrictions imposed by *s* (for example, "bytearray" only
accepts integers that meet the value restriction "0 <= x <= 255").

+--------------------------------+----------------------------------+-----------------------+
| Operation                      | Result                           | Notes                 |
+================================+==================================+=======================+
| "s[i] = x"                     | item *i* of *s* is replaced by   |                       |
|                                | *x*                              |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s[i:j] = t"                   | slice of *s* from *i* to *j* is  |                       |
|                                | replaced by the contents of the  |                       |
|                                | iterable *t*                     |                       |
+--------------------------------+----------------------------------+-----------------------+
| "del s[i:j]"                   | same as "s[i:j] = []"            |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s[i:j:k] = t"                 | the elements of "s[i:j:k]" are   | (1)                   |
|                                | replaced by those of *t*         |                       |
+--------------------------------+----------------------------------+-----------------------+
| "del s[i:j:k]"                 | removes the elements of          |                       |
|                                | "s[i:j:k]" from the list         |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.append(x)"                  | appends *x* to the end of the    |                       |
|                                | sequence (same as                |                       |
|                                | "s[len(s):len(s)] = [x]")        |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.clear()"                    | removes all items from "s" (same | (5)                   |
|                                | as "del s[:]")                   |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.copy()"                     | creates a shallow copy of "s"    | (5)                   |
|                                | (same as "s[:]")                 |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.extend(t)" or "s += t"      | extends *s* with the contents of |                       |
|                                | *t* (for the most part the same  |                       |
|                                | as "s[len(s):len(s)] = t")       |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s *= n"                       | updates *s* with its contents    | (6)                   |
|                                | repeated *n* times               |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.insert(i, x)"               | inserts *x* into *s* at the      |                       |
|                                | index given by *i* (same as      |                       |
|                                | "s[i:i] = [x]")                  |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.pop([i])"                   | retrieves the item at *i* and    | (2)                   |
|                                | also removes it from *s*         |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.remove(x)"                  | remove the first item from *s*   | (3)                   |
|                                | where "s[i] == x"                |                       |
+--------------------------------+----------------------------------+-----------------------+
| "s.reverse()"                  | reverses the items of *s* in     | (4)                   |
|                                | place                            |                       |
+--------------------------------+----------------------------------+-----------------------+

Notes:

1. *t* must have the same length as the slice it is replacing.

2. The optional argument *i* defaults to "-1", so that by default
   the last item is removed and returned.

3. "remove" raises "ValueError" when *x* is not found in *s*.

4. The "reverse()" method modifies the sequence in place for
   economy of space when reversing a large sequence.  To remind users
   that it operates by side effect, it does not return the reversed
   sequence.

5. "clear()" and "copy()" are included for consistency with the
   interfaces of mutable containers that don't support slicing
   operations (such as "dict" and "set")

   New in version 3.3: "clear()" and "copy()" methods.

6. The value *n* is an integer, or an object implementing
   "__index__()".  Zero and negative values of *n* clear the sequence.
   Items in the sequence are not copied; they are referenced multiple
   times, as explained for "s * n" under Common Sequence Operations.
"""
    , 'unary':
    """Unary arithmetic and bitwise operations
***************************************

All unary arithmetic and bitwise operations have the same priority:

   u_expr ::= power | "-" u_expr | "+" u_expr | "~" u_expr

The unary "-" (minus) operator yields the negation of its numeric
argument.

The unary "+" (plus) operator yields its numeric argument unchanged.

The unary "~" (invert) operator yields the bitwise inversion of its
integer argument.  The bitwise inversion of "x" is defined as
"-(x+1)".  It only applies to integral numbers.

In all three cases, if the argument does not have the proper type, a
"TypeError" exception is raised.
"""
    , 'while':
    """The "while" statement
*********************

The "while" statement is used for repeated execution as long as an
expression is true:

   while_stmt ::= "while" expression ":" suite
                  ["else" ":" suite]

This repeatedly tests the expression and, if it is true, executes the
first suite; if the expression is false (which may be the first time
it is tested) the suite of the "else" clause, if present, is executed
and the loop terminates.

A "break" statement executed in the first suite terminates the loop
without executing the "else" clause's suite.  A "continue" statement
executed in the first suite skips the rest of the suite and goes back
to testing the expression.
"""
    , 'with':
    """The "with" statement
********************

The "with" statement is used to wrap the execution of a block with
methods defined by a context manager (see section With Statement
Context Managers). This allows common "try"..."except"..."finally"
usage patterns to be encapsulated for convenient reuse.

   with_stmt ::= "with" with_item ("," with_item)* ":" suite
   with_item ::= expression ["as" target]

The execution of the "with" statement with one "item" proceeds as
follows:

1. The context expression (the expression given in the "with_item")
   is evaluated to obtain a context manager.

2. The context manager's "__exit__()" is loaded for later use.

3. The context manager's "__enter__()" method is invoked.

4. If a target was included in the "with" statement, the return
   value from "__enter__()" is assigned to it.

   Note: The "with" statement guarantees that if the "__enter__()"
     method returns without an error, then "__exit__()" will always be
     called. Thus, if an error occurs during the assignment to the
     target list, it will be treated the same as an error occurring
     within the suite would be. See step 6 below.

5. The suite is executed.

6. The context manager's "__exit__()" method is invoked.  If an
   exception caused the suite to be exited, its type, value, and
   traceback are passed as arguments to "__exit__()". Otherwise, three
   "None" arguments are supplied.

   If the suite was exited due to an exception, and the return value
   from the "__exit__()" method was false, the exception is reraised.
   If the return value was true, the exception is suppressed, and
   execution continues with the statement following the "with"
   statement.

   If the suite was exited for any reason other than an exception, the
   return value from "__exit__()" is ignored, and execution proceeds
   at the normal location for the kind of exit that was taken.

With more than one item, the context managers are processed as if
multiple "with" statements were nested:

   with A() as a, B() as b:
       suite

is equivalent to

   with A() as a:
       with B() as b:
           suite

Changed in version 3.1: Support for multiple context expressions.

See also:

  **PEP 343** - The "with" statement
     The specification, background, and examples for the Python "with"
     statement.
"""
    , 'yield':
    """The "yield" statement
*********************

   yield_stmt ::= yield_expression

A "yield" statement is semantically equivalent to a yield expression.
The yield statement can be used to omit the parentheses that would
otherwise be required in the equivalent yield expression statement.
For example, the yield statements

   yield <expr>
   yield from <expr>

are equivalent to the yield expression statements

   (yield <expr>)
   (yield from <expr>)

Yield expressions and statements are only used when defining a
*generator* function, and are only used in the body of the generator
function.  Using yield in a function definition is sufficient to cause
that definition to create a generator function instead of a normal
function.

For full details of "yield" semantics, refer to the Yield expressions
section.
"""
    }
