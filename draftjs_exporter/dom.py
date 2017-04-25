from __future__ import absolute_import, unicode_literals

import inspect
import re

from draftjs_exporter.engines.html5lib import DOM_HTML5LIB
from draftjs_exporter.error import ConfigException

# Python 2/3 unicode compatibility hack.
# See http://stackoverflow.com/questions/6812031/how-to-make-unicode-string-with-python3
try:
    UNICODE_EXISTS = bool(type(unicode))
except NameError:
    def unicode(s):
        return str(s)

# https://gist.github.com/yahyaKacem/8170675
_first_cap_re = re.compile(r'(.)([A-Z][a-z]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')


class DOM(object):
    """
    Component building API, abstracting the DOM implementation.
    """

    HTML5LIB = 'html5lib'
    LXML = 'lxml'

    dom = DOM_HTML5LIB

    @staticmethod
    def camel_to_dash(camel_cased_str):
        sub2 = _first_cap_re.sub(r'\1-\2', camel_cased_str)
        dashed_case_str = _all_cap_re.sub(r'\1-\2', sub2).lower()
        return dashed_case_str.replace('--', '-')

    @classmethod
    def use(cls, engine=DOM_HTML5LIB):
        """
        Choose which DOM implementation to use.
        """
        if engine:
            if inspect.isclass(engine):
                cls.dom = engine
            elif engine.lower() == cls.HTML5LIB:
                cls.dom = DOM_HTML5LIB
            elif engine.lower() == cls.LXML:
                from draftjs_exporter.engines.lxml import DOM_LXML
                cls.dom = DOM_LXML
            else:
                raise ConfigException('Invalid DOM engine.')

    @classmethod
    def create_element(cls, type_=None, props=None, *children):
        """
        Signature inspired by React.createElement.
        createElement(
          string/Component type,
          [dict props],
          [children ...]
        )
        https://facebook.github.io/react/docs/top-level-api.html#react.createelement
        """
        if props is None:
            props = {}

        if not type_:
            return cls.dom.create_tag('fragment')
        else:
            if len(children) and isinstance(children[0], (list, tuple)):
                children = children[0]

            if inspect.isclass(type_):
                props['children'] = children[0] if len(children) == 1 else children
                elt = type_().render(props)
            elif callable(getattr(type_, 'render', None)):
                props['children'] = children[0] if len(children) == 1 else children
                elt = type_.render(props)
            elif callable(type_):
                props['children'] = children[0] if len(children) == 1 else children
                elt = type_(props)
            else:
                # Never render those attributes on a raw tag.
                props.pop('children', None)
                props.pop('block', None)
                props.pop('entity', None)

                if 'style' in props and isinstance(props['style'], dict):
                    rules = ['{0}: {1};'.format(DOM.camel_to_dash(s), props['style'][s]) for s in props['style'].keys()]
                    props['style'] = ''.join(sorted(rules))

                # Map props from React/Draft.js to HTML lingo.
                if 'className' in props:
                    props['class'] = props.pop('className')

                attributes = {}
                for key in props:
                    if props[key] is False:
                        props[key] = 'false'

                    if props[key] is True:
                        props[key] = 'true'

                    if props[key] is not None:
                        attributes[key] = unicode(props[key])

                elt = cls.dom.create_tag(type_, attributes)

                for child in children:
                    if child not in (None, ''):
                        cls.append_child(elt, child)

        if elt in (None, ''):
            elt = cls.dom.create_tag('fragment')

        return elt

    @classmethod
    def parse_html(cls, markup):
        return cls.dom.parse_html(markup)

    @classmethod
    def append_child(cls, elt, child):
        return cls.dom.append_child(elt, child)

    @classmethod
    def render(cls, elt):
        return cls.dom.render(elt)

    @classmethod
    def render_debug(cls, elt):
        return cls.dom.render_debug(elt)
