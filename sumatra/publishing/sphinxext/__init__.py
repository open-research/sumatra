"""


:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

from .sumatra_rst import SumatraImage, smt_link_role


def setup(app):
    app.add_config_value('sumatra_record_store', None, 'env')
    app.add_config_value('sumatra_project', None, 'env')
    app.add_config_value('sumatra_link_icon', 'icon_info.png', 'html')
    app.add_directive('smtimage', SumatraImage)
    app.add_role('smtlink', smt_link_role)
    # app.connect('env-purge-doc', purge_smtimages)  # do we need this?
