"""Seed PostGIS (`make seed`).

Phase 1 upserts the candidate basin polygons. Phase 2 adds the platform registry and
reference layers.
"""

from geoalchemy2.shape import from_shape
from sqlalchemy.dialects.postgresql import insert

from pipeline.basins import BASINS
from pipeline.db.models import SRID, Basin
from pipeline.db.session import get_sessionmaker


def seed_basins() -> int:
    rows = [
        {"id": bid, "name": name, "geom": from_shape(poly, srid=SRID)}
        for bid, (name, poly) in BASINS.items()
    ]
    stmt = insert(Basin).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Basin.id], set_={"name": stmt.excluded.name, "geom": stmt.excluded.geom}
    )
    with get_sessionmaker()() as session, session.begin():
        session.execute(stmt)
    return len(rows)


def main() -> None:
    print(f"seeded {seed_basins()} basins")


if __name__ == "__main__":
    main()
