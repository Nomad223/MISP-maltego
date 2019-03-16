from canari.maltego.transform import Transform
# from canari.framework import EnableDebugWindow
from MISP_maltego.transforms.common.entities import MISPEvent, MISPGalaxy
from MISP_maltego.transforms.common.util import get_misp_connection, galaxycluster_to_entity, get_galaxy_cluster, get_galaxies_relating, mapping_galaxy_icon
from canari.maltego.message import UIMessageType, UIMessage


__author__ = 'Christophe Vandeplas'
__copyright__ = 'Copyright 2018, MISP_maltego Project'
__credits__ = []

__license__ = 'AGPLv3'
__version__ = '0.1'
__maintainer__ = 'Christophe Vandeplas'
__email__ = 'christophe@vandeplas.com'
__status__ = 'Development'


# @EnableDebugWindow
class GalaxyToEvents(Transform):
    """Expands a Galaxy to multiple MISP Events."""

    # The transform input entity type.
    input_type = MISPGalaxy

    def do_transform(self, request, response, config):
        maltego_misp_galaxy = request.entity
        misp = get_misp_connection(config)
        if maltego_misp_galaxy.tag_name:
            tag_name = maltego_misp_galaxy.tag_name
        else:
            tag_name = maltego_misp_galaxy.value
        events_json = misp.search(controller='events', tags=tag_name, withAttachments=False)
        for e in events_json['response']:
            response += MISPEvent(e['Event']['id'], uuid=e['Event']['uuid'], info=e['Event']['info'])
        return response

    def on_terminate(self):
        """This method gets called when transform execution is prematurely terminated. It is only applicable for local
        transforms. It can be excluded if you don't need it."""
        pass


# @EnableDebugWindow
class GalaxyToRelations(Transform):
    """Expans a Galaxy to related Galaxies and Clusters"""
    input_type = MISPGalaxy

    def do_transform(self, request, response, config):
        maltego_misp_galaxy = request.entity

        if maltego_misp_galaxy.uuid:
            current_cluster = get_galaxy_cluster(uuid=maltego_misp_galaxy.uuid)
        elif maltego_misp_galaxy.tag_name:
            current_cluster = get_galaxy_cluster(tag=maltego_misp_galaxy.tag_name)
        elif maltego_misp_galaxy.name:
            current_cluster = get_galaxy_cluster(tag=maltego_misp_galaxy.name)

        if not current_cluster:
            response += UIMessage("Galaxy Cluster UUID not in local mapping. Please update local cache; non-public UUID are not supported yet.", type=UIMessageType.Inform)
            return response
        c = current_cluster
        # update existing object
        # import json
        # print(json.dumps(c, sort_keys=True, indent=2))
        # return response
        galaxy_cluster = get_galaxy_cluster(c['uuid'])
        icon_url = None
        import os
        if 'icon' in galaxy_cluster:  # LATER further investigate if using icons locally is a good idea.
            # map the 'icon' name from the cluster to the icon filename of the intelligence-icons repository
            try:
                icon_url = 'file://{}/{}.png'.format(os.path.join(os.getcwd(), 'MISP_maltego', 'resources', 'images', 'intelligence-icons'), mapping_galaxy_icon[galaxy_cluster['icon']])
            except Exception:
                # it's not in our mapping, just ignore and leave the default Galaxy icon
                pass
        if c['meta'].get('synonyms'):
            synonyms = ', '.join(c['meta']['synonyms'])
        else:
            synonyms = ''
        request.entity.name = '{}\n{}'.format(c['type'], c['value'])
        request.entity.uuid = c['uuid']
        request.entity.description = c.get('description')
        request.entity.cluster_type = c.get('type')
        request.entity.cluster_value = c.get('value')
        request.entity.synonyms = synonyms
        request.entity.tag_name = c['tag_name']
        request.entity.icon_url = icon_url
        # response += request.entity
        # find related objects
        if 'related' in current_cluster:
            for related in current_cluster['related']:
                related_cluster = get_galaxy_cluster(related['dest-uuid'])
                if related_cluster:
                    response += galaxycluster_to_entity(related_cluster, link_label=related['type'])
        # find objects that are relating to this one
        # for related in get_galaxies_relating(current_cluster['uuid']):
        #     response += galaxycluster_to_entity(related, link_label="FIXME opposite of ".format(related['type']))  # FIXME link_label should be opposite
        return response
