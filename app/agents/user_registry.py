from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Literal

PlanName = Literal["GOLD", "SILVER", "BRONZE"]

@dataclass
class UserProfile:
	company_name: str
	user_name: str
	data_plan: PlanName
	email: str
	uid: str
	last_date_modified: datetime

	def to_dict(self) -> Dict:
		d = asdict(self)
		d["last_date_modified"] = self.last_date_modified.isoformat()
		return d


def _start_of_current_month() -> datetime:
	now = datetime.now(timezone.utc)
	return datetime(year=now.year, month=now.month, day=1, tzinfo=timezone.utc)


# In-memory mock user registry
_USERS: Dict[str, UserProfile] = {}
_USERS_BY_UID: Dict[str, UserProfile] = {}


def _add_user(profile: UserProfile) -> None:
	_USERS[profile.user_name.lower()] = profile
	_USERS_BY_UID[profile.uid] = profile


# Seed mock users
_seed_date = _start_of_current_month()
_add_user(
	UserProfile(
		company_name="Fargo Bank",
		user_name="alice",
		data_plan="GOLD",
		email="alice@fargobank.com",
		uid="U1001",
		last_date_modified=_seed_date,
	)
)
_add_user(
	UserProfile(
		company_name="Fargo Bank",
		user_name="bob",
		data_plan="SILVER",
		email="bob@fargobank.com",
		uid="U1002",
		last_date_modified=_seed_date,
	)
)
_add_user(
	UserProfile(
		company_name="Fargo Bank",
		user_name="charlie",
		data_plan="BRONZE",
		email="charlie@fargobank.com",
		uid="U1003",
		last_date_modified=_seed_date,
	)
)

# Appended users from user request
_add_user(
    UserProfile(
        company_name="LUMN-5577",
        user_name="USR-AstroZen",
        data_plan="GOLD",
        email="USR-AstroZen@LUMN-5577.com",
        uid="U1004",
        last_date_modified=_seed_date,
    )
)
_add_user(
    UserProfile(
        company_name="QUAS-3344",
        user_name="USR-NebulaX",
        data_plan="GOLD",
        email="USR-NebulaX@QUAS-3344.com",
        uid="U1005",
        last_date_modified=_seed_date,
    )
)
_add_user(
    UserProfile(
        company_name="CMPX-9012",
        user_name="USR-ApolloX",
        data_plan="GOLD",
        email="USR-ApolloX@CMPX-9012.com",
        uid="U1006",
        last_date_modified=_seed_date,
    )
)
_add_user(
    UserProfile(
        company_name="VRTX-6633",
        user_name="USR-StellarQ",
        data_plan="GOLD",
        email="USR-StellarQ@VRTX-6633.com",
        uid="U1007",
        last_date_modified=_seed_date,
    )
)
_add_user(
    UserProfile(
        company_name="STRM-8822",
        user_name="USR-Galactiq",
        data_plan="GOLD",
        email="USR-Galactiq@STRM-8822.com",
        uid="U1008",
        last_date_modified=_seed_date,
    )
)
_add_user(
    UserProfile(
        company_name="NOVA-7788",
        user_name="USR-OrionEdge",
        data_plan="BRONZE",
        email="USR-OrionEdge@NOVA-7788.com",
        uid="U1009",
        last_date_modified=_seed_date,
    )
)
_add_user(
    UserProfile(
        company_name="PLSM-2201",
        user_name="USR-Solarix",
        data_plan="BRONZE",
        email="USR-Solarix@PLSM-2201.com",
        uid="U1010",
        last_date_modified=_seed_date,
    )
)
_add_user(
    UserProfile(
        company_name="CRYX-9900",
        user_name="USR-Meteorix",
        data_plan="BRONZE",
        email="USR-Meteorix@CRYX-9900.com",
        uid="U1011",
        last_date_modified=_seed_date,
    )
)
_add_user(
    UserProfile(
        company_name="ZEN-4521",
        user_name="USR-LunaSky",
        data_plan="SILVER",
        email="USR-LunaSky@ZEN-4521.com",
        uid="U1012",
        last_date_modified=_seed_date,
    )
)
_add_user(
    UserProfile(
        company_name="AURA-1199",
        user_name="USR-Cosmosia",
        data_plan="SILVER",
        email="USR-Cosmosia@AURA-1199.com",
        uid="U1013",
        last_date_modified=_seed_date,
    )
)


def get_user_profile(user_name: str) -> Optional[Dict]:
	"""Fetch a user's profile by username (case-insensitive). Returns dict or None."""
	profile = _USERS.get(user_name.lower())
	return profile.to_dict() if profile else None


def set_user_plan(uid: str, plan: str) -> bool:
	"""Update the user's data plan by uid. Only allows GOLD, SILVER, BRONZE.

	Returns True if updated, False if user not found or plan invalid.
	"""
	plan_upper = plan.upper()
	if plan_upper not in ("GOLD", "SILVER", "BRONZE"):
		return False

	profile = _USERS_BY_UID.get(uid)
	if not profile:
		return False

	if profile.data_plan == plan_upper:
		# No change needed
		return True

	profile.data_plan = plan_upper  # type: ignore[assignment]
	profile.last_date_modified = datetime.now(timezone.utc)
	return True


def list_users() -> List[Dict]:
	"""Return all users as a list of dicts (for debugging)."""
	return [u.to_dict() for u in _USERS.values()]

