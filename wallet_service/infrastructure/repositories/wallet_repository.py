from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from wallet_service.domain.interfaces.wallet_repository import IWalletRepository
from wallet_service.domain.models.wallet import NetworkType, Wallet
from wallet_service.infrastructure.database.models import WalletModel


class WalletRepository(IWalletRepository):
    """Repository implementation backed by PostgreSQL via SQLAlchemy async."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, wallet: Wallet) -> Wallet:
        """Create new wallet."""
        db_wallet = WalletModel(
            user_id=wallet.user_id,
            network=wallet.network.value,
            wallet_address=wallet.wallet_address,
            derivation_index=wallet.derivation_index,
            created_at=wallet.created_at
        )

        self.session.add(db_wallet)
        await self.session.flush()

        wallet.id = db_wallet.id
        return wallet

    async def get_by_user_and_network(self, user_id: str, network: str) -> Wallet | None:
        """Get wallet by user and network."""
        stmt = select(WalletModel).where(
            and_(WalletModel.user_id == user_id, WalletModel.network == network)
        )

        result = await self.session.execute(stmt)
        db_wallet = result.scalar_one_or_none()

        return self._to_domain(db_wallet) if db_wallet else None

    async def get_next_derivation_index(self, network: str) -> int:
        """Get next available derivation index."""
        stmt = select(func.max(WalletModel.derivation_index)).where(WalletModel.network == network)
        result = await self.session.execute(stmt)
        max_index = result.scalar_one()
        return 0 if max_index is None else max_index + 1

    async def exists(self, user_id: str, network: str) -> bool:
        """Check if wallet exists."""
        stmt = select(WalletModel.id).where(
            and_(WalletModel.user_id == user_id, WalletModel.network == network)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update_last_accessed(self, wallet_id: UUID) -> None:
        """Update last accessed timestamp."""
        stmt = update(WalletModel).where(WalletModel.id == wallet_id).values(last_accessed_at=datetime.now())
        await self.session.execute(stmt)

    def _to_domain(self, db_wallet: WalletModel) -> Wallet:
        """Convert database model to domain model."""
        wallet = Wallet(
            user_id=db_wallet.user_id,
            network=NetworkType(db_wallet.network),
            wallet_address=db_wallet.wallet_address,
            derivation_index=db_wallet.derivation_index
        )
        wallet.id = db_wallet.id
        wallet.created_at = db_wallet.created_at
        wallet.last_accessed_at = db_wallet.last_accessed_at
        return wallet
