from backend.tests.factories.dictionary_entry import DictionaryEntryFactory
from backend.tests.factories.site_info_factories import SiteFeatureFactory


class ControlledSiteContentFactory(DictionaryEntryFactory):
    # use any concrete model that inherits from BaseControlledSiteContentModel
    pass


class UncontrolledSiteContentFactory(SiteFeatureFactory):
    # use any concrete model that inherits from BaseSiteContentModel
    pass
