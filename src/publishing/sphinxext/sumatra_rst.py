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

"""

from docutils.parsers.rst import directives, states
from docutils.parsers.rst.directives.images import Image
from docutils.parsers.rst.roles import set_classes
from docutils.parsers.rst import roles
from docutils import nodes, utils

from sumatra.projects import load_project
from sumatra.recordstore import get_record_store
from sumatra.datastore import DataKey
import os.path


def smt_link_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    label = text
    settings = inliner.document.settings
    ref = "%s/%s/%s/" % (settings.sumatra_record_store,
                         settings.sumatra_project_name,
                         label)
    set_classes(options)
    node = nodes.reference(rawtext, '', refuri=ref,
                           **options)
    node += nodes.image(uri=settings.sumatra_link_icon, alt='smt:' + utils.unescape(text))
    return [node], []

roles.register_local_role('smtlink', smt_link_role)


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

        if hasattr(self.state.document.settings, 'env'):  # using sphinx
            config = self.state.document.settings.env.config
        else:
            config = self.state.document.settings         # using plain docutils
        
        # determine which record store to use
        if hasattr(config, 'sumatra_project_dir'):
            prj = load_project(config.sumatra_project_dir)
        elif os.path.exists(os.path.join('.smt', 'project')):
            prj = load_project()
        else:
            prj = None
        if 'record_store' in self.options:
            record_store = get_record_store(self.options["record_store"])
        elif hasattr(config, 'sumatra_record_store'):
            record_store = get_record_store(config.sumatra_record_store)
        elif prj is None:
            raise self.error(
                'Neither project_dir nor record_store defined'
            )
        else:
            record_store = prj.record_store
        
        # determine the project (short) name
        if 'project' in self.options:
            project_name = self.options['project']
        elif hasattr(config, 'sumatra_project_name'):
            project_name = config.sumatra_project_name
        elif prj is None:
            raise self.error('project name not defined')
        else:
            project_name = prj.name
        
        record_label = self.arguments[0]
        record = record_store.get(project_name, record_label)
        if len(self.arguments) == 2:
            raise NotImplementedError
        else:
            image_file = record.output_data[0]
        assert isinstance(image_file, DataKey), type(image_file)
        
        # check digest, if supplied
        if 'digest' in self.options:
            if self.options['digest'] != image_file.digest:
                raise self.error('Digests do not match')
        
        if hasattr(image_file, 'url'):
            reference = image_file.url
        else:
            reference = "http://data.andrewdavison.info/Destexhe_JCNS_2009/" + image_file.path  ## temporary hack
            #raise NotImplementedError  # get file content, write local temporary file
        
        # set values for alt and target, if they have not been specified
        if not 'target' in self.options and hasattr(record_store, 'server_url'):
            self.options['target'] = "%s%s/%s/" % (record_store.server_url, project_name, record_label)
        if not 'alt' in self.options:
            self.options['alt'] = "Data file generated by computation %s" % record_label
        
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
