from abc import ABC, abstractmethod

class EmailSenderInterface(ABC):
    @abstractmethod
    async def send_activation_email(self, email: str, activation_link: str) -> None:
        """Asynchronously send an account activation email."""
        pass

    @abstractmethod
    async def send_activation_complete_email(self, email: str, login_link: str) -> None:
        """Asynchronously send an email confirming account activation."""
        pass

    @abstractmethod
    async def send_password_reset_email(self, email: str, reset_link: str) -> None:
        """Asynchronously send a password reset request email."""
        pass

    @abstractmethod
    async def send_password_reset_complete_email(self, email: str, login_link: str) -> None:
        """Asynchronously send an email confirming password reset."""
        pass