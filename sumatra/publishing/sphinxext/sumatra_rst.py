"""
idea for an "smtimage" directive (and "smtfigure" similarly) which would be used
like

.. smtimage:: 20120907-153528 demo_cx05_N=500b_LTS_d274f9660531.png
   :project: Destexhe_JCNS_2009
   :record_store: /path/to/recordstore/file or http://smt.andrewdavison.info/records
   :digest: DIGEST_GOES_HERE_FOR_CHECKING (optional)

This would query the recordstore, make a copy of the image file in a temporary
directory, and preferably clean up the temporary directory later (use "pending" node?).
If using a MirroredFileSystemDataStore could just use URL

The project name and recordstore directive are optional if rst2xxxx is used in a Sumatra project directory


:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

from docutils.parsers.rst import directives, states
from docutils.parsers.rst.directives.images import Image
from docutils.parsers.rst.roles import set_classes
from docutils.parsers.rst import roles
from docutils import nodes, utils

from sumatra.publishing.utils import determine_project, determine_record_store, \
    determine_project_name, record_link_url, \
    get_image, get_record_label_and_image_path
import os.path


LOCAL_IMAGE_CACHE = "smt_images"  # should use tempfile?


def smt_link_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    label = text
    settings = inliner.document.settings
    ref = "%s/%s/%s/" % (settings.sumatra_record_store,
                         settings.sumatra_project,
                         label)
    set_classes(options)
    node = nodes.reference(rawtext, '', refuri=ref,
                           **options)
    node += nodes.image(uri=settings.sumatra_link_icon, alt='smt:' + utils.unescape(text))
    return [node], []

roles.register_local_role('smtlink', smt_link_role)


def build_options(global_settings, local_options):
    if hasattr(global_settings, 'env'):  # using sphinx
        config = global_settings.env.config
    else:
        config = global_settings         # using plain docutils
    # convert config into dict, and strip "sumatra_" prefix
    combined_options = {}
    for name in ("record_store", "project", "link_icon"):
        full_name = "sumatra_" + name
        if hasattr(config, full_name):
            combined_options[name] = getattr(config, full_name)
    combined_options.update(local_options)
    return combined_options


class SumatraImage(Image):

    required_arguments = 1  # Sumatra label
    optional_arguments = 1  # path to image file. Not required if record has only a single image file as output
    final_argument_whitespace = False
    option_spec = {'alt': directives.unchanged,
                   'height': directives.length_or_unitless,
                   'width': directives.length_or_percentage_or_unitless,
                   'scale': directives.percentage,
                   'align': lambda argument: directives.choice(argument, Image.align_values),
                   'name': directives.unchanged,
                   'target': directives.unchanged_required,
                   'class': directives.class_option,
                   'project': directives.unchanged,
                   'record_store': directives.unchanged,
                   'digest': directives.unchanged,
                   }

    def run(self):
        if 'align' in self.options:
            if isinstance(self.state, states.SubstitutionDef):
                # Check for align_v_values.
                if self.options['align'] not in self.align_v_values:
                    raise self.error(
                        'Error in "%s" directive: "%s" is not a valid value '
                        'for the "align" option within a substitution '
                        'definition.  Valid values for "align" are: "%s".'
                        % (self.name, self.options['align'],
                           '", "'.join(self.align_v_values)))
            elif self.options['align'] not in self.align_h_values:
                raise self.error(
                    'Error in "%s" directive: "%s" is not a valid value for '
                    'the "align" option.  Valid values for "align" are: "%s".'
                    % (self.name, self.options['align'],
                       '", "'.join(self.align_h_values)))
        messages = []
        # previous code from Image.run()
        # --------------------------------------------------------------------

        sumatra_options = build_options(self.state.document.settings, self.options)

        # determine which record store to use
        prj = determine_project(sumatra_options)
        record_store = determine_record_store(prj, sumatra_options, self.error)

        # determine the project (short) name
        project_name = determine_project_name(prj, sumatra_options, self.error)

        record_label, image_path = get_record_label_and_image_path(self.arguments[0])
        record = record_store.get(project_name, record_label)
        image = get_image(record, image_path, self.options, self.error)  # automatically checks digest
        if hasattr(image, "url"):
            reference = image.url
        else:
            if not os.path.exists(LOCAL_IMAGE_CACHE):
                os.makedirs(LOCAL_IMAGE_CACHE)
            reference = image.save_copy(LOCAL_IMAGE_CACHE)

        # set values for alt and target, if they have not been specified
        if not 'target' in self.options and hasattr(record_store, 'server_url'):
            self.options['target'] = record_link_url(record_store.server_url, project_name, record_label)
        if not 'alt' in self.options:
            self.options['alt'] = "Data file generated by computation %s" % record_label

        # --------------------------------------------------------------------
        # following code from Image.run()
        self.options['uri'] = reference
        reference_node = None
        if 'target' in self.options:
            block = states.escape2null(
                self.options['target']).splitlines()
            block = [line for line in block]
            target_type, data = self.state.parse_target(
                block, self.block_text, self.lineno)
            if target_type == 'refuri':
                reference_node = nodes.reference(refuri=data)
            elif target_type == 'refname':
                reference_node = nodes.reference(
                    refname=fully_normalize_name(data),
                    name=whitespace_normalize_name(data))
                reference_node.indirect_reference_name = data
                self.state.document.note_refname(reference_node)
            else:                           # malformed target
                messages.append(data)       # data is a system message
            del self.options['target']
        set_classes(self.options)
        image_node = nodes.image(self.block_text, **self.options)
        self.add_name(image_node)
        if reference_node:
            reference_node += image_node
            return messages + [reference_node]
        else:
            return messages + [image_node]


directives.register_directive("smtimage", SumatraImage)

# possible glyphicons for links to record store
# icon-search
# icon-file
# icon-bookmark
# icon-info-sign
# icon-comment
# icon-book
