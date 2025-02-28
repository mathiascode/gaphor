"""Common dependencies like dependency, usage, implementation and realization.

Dependency Type
===============
Dependency type should be determined automatically by default. User should
be able to override the dependency type.

When dependency item is connected between two items, then type of the
dependency cannot be changed. For example, if two class items are
connected, then dependency type cannot be changed to realization as this
dependency type can only exist between a component and a classifier.

Function dependency_type in model factory should be used to determine
type of a dependency in automatic way.
"""

from gaphor import UML
from gaphor.core import gettext
from gaphor.core.modeling.properties import attribute
from gaphor.diagram.presentation import LinePresentation, Named
from gaphor.diagram.shapes import Box, Text, stroke
from gaphor.diagram.support import represents
from gaphor.UML.classes.interface import Folded, InterfacePort
from gaphor.UML.recipes import stereotypes_str


@represents(UML.Dependency, head=UML.Dependency.supplier, tail=UML.Dependency.client)
class DependencyItem(Named, LinePresentation):
    """Dependency item represents several types of dependencies, i.e. normal
    dependency or usage.

    Usually a dependency looks like a dashed line with an arrow head.
    The dependency can have a stereotype attached to it, stating the kind of
    dependency we're dealing with.

    In case of usage dependency connected to folded interface, the line is
    drawn as solid line without arrow head.
    """

    def __init__(self, diagram, id=None):

        additional_stereotype = {
            UML.Usage: (gettext("use"),),
            UML.Realization: (gettext("realize"),),
            UML.InterfaceRealization: (gettext("implements"),),
        }

        self._dependency_type = UML.Dependency

        super().__init__(
            diagram,
            id,
            shape_middle=Box(
                Text(
                    text=lambda: stereotypes_str(
                        self.subject,
                        additional_stereotype.get(self._dependency_type, ()),
                    ),
                ),
                Text(text=lambda: self.subject.name or ""),
            ),
        )

        self._handles[0].pos = (30, 20)
        self._handles[1].pos = (0, 0)

        self.watch("subject[NamedElement].name")
        self.watch("subject.appliedStereotype.classifier.name")

    auto_dependency: attribute[int] = attribute("auto_dependency", int, default=True)

    def postload(self):
        if self.subject:
            self._dependency_type = self.subject.__class__
        super().postload()

    @property
    def on_folded_interface(self):
        connection = self._connections.get_connection(self.head)
        return (
            "true"
            if (
                connection
                and isinstance(connection.port, InterfacePort)
                and connection.connected.folded != Folded.NONE
            )
            else "false"
        )

    def set_dependency_type(self, dependency_type):
        self._dependency_type = dependency_type

    dependency_type = property(lambda s: s._dependency_type, set_dependency_type)

    def draw_head(self, context):
        cr = context.cairo
        if context.style.get("dash-style"):
            cr.set_dash((), 0)
            cr.move_to(15, -6)
            cr.line_to(0, 0)
            cr.line_to(15, 6)
            stroke(context, dash=False)
        cr.move_to(0, 0)
