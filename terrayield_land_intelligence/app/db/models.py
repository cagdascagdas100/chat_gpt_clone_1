from __future__ import annotations

class _ColumnShim:
    def asc(self):
        return self

    def desc(self):
        return self

    def is_not(self, _value):
        return self


class _ModelShim:
    id = _ColumnShim()
    source_name = _ColumnShim()
    fetched_at = _ColumnShim()
    source_updated_at = _ColumnShim()
    row_count = _ColumnShim()
    metadata_json = _ColumnShim()
    local_authority = _ColumnShim()
    geometry = _ColumnShim()


class SourceSnapshot(_ModelShim):
    pass


class DQIssue(_ModelShim):
    pass


class ListingParcelLink(_ModelShim):
    pass


class ListingsGovernmentPropertyFinder(_ModelShim):
    pass


class ListingsLandHub(_ModelShim):
    pass


class ListingsMarketAdapter(_ModelShim):
    pass


class ManualMatchOverride(_ModelShim):
    pass


class ParcelInspire(_ModelShim):
    pass


class SitesBrownfieldLocalAuthority(_ModelShim):
    pass


class SitesBrownfieldPlanningData(_ModelShim):
    pass


class TransactionsPricePaid(_ModelShim):
    pass
