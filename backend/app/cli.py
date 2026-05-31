"""Admin command-line utilities.

Create or promote an admin account (run inside the api container):

    docker compose -f docker-compose.prod.yml exec api \\
        python -m app.cli create-admin --email you@example.com --password 'StrongPass123' --name 'Admin'

If the email already exists, the account is promoted to admin (and marked verified); pass
``--password`` to also reset its password.
"""

import argparse
import asyncio

from app.core.db import get_sessionmaker, init_engine
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


async def create_admin(email: str, password: str | None, name: str | None) -> None:
    init_engine()
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        repo = UserRepository(session)
        user = await repo.get_by_email(email.lower())
        if user is not None:
            user.is_admin = True
            user.is_verified = True
            if password:
                user.hashed_password = hash_password(password)
            action = "promoted to admin"
        else:
            if not password:
                raise SystemExit("A new admin account requires --password")
            user = await repo.add(
                User(
                    email=email.lower(),
                    hashed_password=hash_password(password),
                    full_name=name,
                    is_verified=True,
                    is_admin=True,
                    auth_provider="password",
                )
            )
            action = "created as admin"
        await session.commit()
        print(f"✓ {email} {action}.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create-admin", help="Create or promote an admin user")
    p.add_argument("--email", required=True)
    p.add_argument("--password", default=None, help="Required when creating a new account")
    p.add_argument("--name", default=None)

    args = parser.parse_args()
    if args.command == "create-admin":
        asyncio.run(create_admin(args.email, args.password, args.name))


if __name__ == "__main__":
    main()
