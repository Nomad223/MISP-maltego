from canari.maltego.entities import Netblock, Unknown
from canari.maltego.transform import Transform
# from canari.framework import EnableDebugWindow
from MISP_maltego.transforms.common.util import get_misp_connection, event_to_entity, get_attribute_in_event, attribute_to_entity

__author__ = 'Christophe Vandeplas'
__copyright__ = 'Copyright 2018, MISP_maltego Project'
__credits__ = []

__license__ = 'AGPLv3'
__version__ = '0.1'
__maintainer__ = 'Christophe Vandeplas'
__email__ = 'christophe@vandeplas.com'
__status__ = 'Development'


# @EnableDebugWindow
class AttributeInMISP(Transform):
    """Green bookmark if known in MISP"""
    display_name = 'in MISP?'
    input_type = Unknown

    def do_transform(self, request, response, config):
        maltego_misp_attribute = request.entity
        # skip MISP Events (value = int)
        try:
            int(maltego_misp_attribute.value)
            return response
        except Exception:
            pass

        misp = get_misp_connection(config)
        events_json = misp.search(controller='events', values=maltego_misp_attribute.value, withAttachments=False)
        in_misp = False
        for e in events_json['response']:
            in_misp = True
            break
        # find the object again, and bookmark it green
        # we need to do really rebuild the Entity from scratch as request.entity is of type Unknown
        if in_misp:
            for e in events_json['response']:
                attr = get_attribute_in_event(e, maltego_misp_attribute.value)
                if attr:
                    for item in attribute_to_entity(attr, only_self=True):
                        response += item
        return response


# placeholder for https://github.com/MISP/MISP-maltego/issues/11
# waiting for support of CIDR search through the REST API
# @EnableDebugWindow
# class NetblockToAttributes(Transform):
#     display_name = 'to MISP Attributes'
#     input_type = Netblock

#     def do_transform(self, request, response, config):
#         maltego_misp_attribute = request.entity
#         misp = get_misp_connection(config)
#         import ipaddress
#         ip_start, ip_end = maltego_misp_attribute.value.split('-')
#         # FIXME make this work with IPv4 and IPv6
#         # automagically detect the different CIDRs
#         cidrs = ipaddress.summarize_address_range(ipaddress.IPv4Address(ip_start), ipaddress.IPv4Address(ip_end))
#         for cidr in cidrs:
#             print(str(cidr))
#             attr_json = misp.search(controller='attributes', values=str(cidr), withAttachments=False)
#             print(attr_json)
#         return response


# @EnableDebugWindow
class AttributeToEvent(Transform):
    display_name = 'to MISP Event'
    input_type = Unknown

    def do_transform(self, request, response, config):
        maltego_misp_attribute = request.entity
        # skip MISP Events (value = int)
        try:
            int(maltego_misp_attribute.value)
            return response
        except Exception:
            pass
        # test for Netblock
        if 'ipv4-range' in request.entity.fields:
            # placeholder for https://github.com/MISP/MISP-maltego/issues/11
            pass

        misp = get_misp_connection(config)
        events_json = misp.search(controller='events', values=maltego_misp_attribute.value, withAttachments=False)
        in_misp = False
        for e in events_json['response']:
            in_misp = True
            response += event_to_entity(e)
        # find the object again, and bookmark it green
        # we need to do really rebuild the Entity from scratch as request.entity is of type Unknown
        if in_misp:
            for e in events_json['response']:
                attr = get_attribute_in_event(e, maltego_misp_attribute.value)
                if attr:
                    for item in attribute_to_entity(attr, only_self=True):
                        response += item
        return response

    def on_terminate(self):
        """This method gets called when transform execution is prematurely terminated. It is only applicable for local
        transforms. It can be excluded if you don't need it."""
        pass
