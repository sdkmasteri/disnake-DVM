# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional

from ..enums import ComponentType
from ..message import Message
from ..utils import cached_slot_property
from .base import ClientT, Interaction

if TYPE_CHECKING:
    from ..state import ConnectionState
    from ..types.interactions import (
        ModalInteraction as ModalInteractionPayload,
        ModalInteractionActionRow as ModalInteractionActionRowPayload,
        ModalInteractionComponentData as ModalInteractionComponentDataPayload,
        ModalInteractionData as ModalInteractionDataPayload,
    )

__all__ = ("ModalInteraction", "ModalInteractionData")


class ModalInteraction(Interaction[ClientT]):
    """Represents an interaction with a modal.

    .. versionadded:: 2.4

    Attributes
    ----------
    id: :class:`int`
        The interaction's ID.
    type: :class:`InteractionType`
        The interaction type.
    application_id: :class:`int`
        The application ID that the interaction was for.
    token: :class:`str`
        The token to continue the interaction.
        These are valid for 15 minutes.
    guild_id: Optional[:class:`int`]
        The guild ID the interaction was sent from.
    channel: Union[:class:`abc.GuildChannel`, :class:`Thread`, :class:`abc.PrivateChannel`, :class:`PartialMessageable`]
        The channel the interaction was sent from.

        Note that due to a Discord limitation, DM channels
        may not contain recipient information.
        Unknown channel types will be :class:`PartialMessageable`.

        .. versionchanged:: 2.10
            If the interaction was sent from a thread and the bot cannot normally access the thread,
            this is now a proper :class:`Thread` object.
            Private channels are now proper :class:`DMChannel`/:class:`GroupChannel`
            objects instead of :class:`PartialMessageable`.

        .. note::
            If you want to compute the interaction author's or bot's permissions in the channel,
            consider using :attr:`permissions` or :attr:`app_permissions`.

    author: Union[:class:`User`, :class:`Member`]
        The user or member that sent the interaction.
    locale: :class:`Locale`
        The selected language of the interaction's author.

        .. versionchanged:: 2.5
            Changed to :class:`Locale` instead of :class:`str`.

    guild_locale: Optional[:class:`Locale`]
        The selected language of the interaction's guild.
        This value is only meaningful in guilds with ``COMMUNITY`` feature and receives a default value otherwise.
        If the interaction was in a DM, then this value is ``None``.

        .. versionchanged:: 2.5
            Changed to :class:`Locale` instead of :class:`str`.

    client: :class:`Client`
        The interaction client.
    entitlements: List[:class:`Entitlement`]
        The entitlements for the invoking user and guild,
        representing access to an application subscription.

        .. versionadded:: 2.10

    authorizing_integration_owners: Dict[:class:`ApplicationIntegrationTypes`, int]
        The authorizing user/guild for the application installation.

        This is only available if the application was installed to a user, and is empty otherwise.
        If this interaction was triggered through an application command,
        this requirement also applies to the command itself; see :attr:`ApplicationCommand.integration_types`.

        The value for the :attr:`ApplicationIntegrationTypes.user` key is the user ID.
        If the application (and command) was also installed to the guild, the value for the
        :attr:`ApplicationIntegrationTypes.guild` key is the guild ID, or ``0`` in DMs with the bot.

        See the :ddocs:`official docs <interactions/receiving-and-responding#interaction-object-authorizing-integration-owners-object>`
        for more information.

        For example, this would return ``{.guild: <guild_id>, .user: <user_id>}`` if invoked in a guild and installed to the guild and user,
        or ``{.user: <user_id>}`` in a DM between two users.

        .. versionadded:: 2.10

    context: Optional[:class:`InteractionContextTypes`]
        The context where the interaction was triggered from.

        This has the same requirements as :attr:`authorizing_integration_owners`; that is,
        this is only available if the application (and command) was installed to a user, and is ``None`` otherwise.

        .. versionadded:: 2.10

    data: :class:`ModalInteractionData`
        The wrapped interaction data.
    message: Optional[:class:`Message`]
        The message that this interaction's modal originated from,
        if the modal was sent in response to a component interaction.

        .. versionadded:: 2.5
    """

    __slots__ = ("message", "_cs_text_values")

    def __init__(self, *, data: ModalInteractionPayload, state: ConnectionState) -> None:
        super().__init__(data=data, state=state)
        self.data: ModalInteractionData = ModalInteractionData(data=data["data"])

        if message_data := data.get("message"):
            message = Message(state=self._state, channel=self.channel, data=message_data)
        else:
            message = None
        self.message: Optional[Message] = message

    def walk_raw_components(self) -> Generator[ModalInteractionComponentDataPayload, None, None]:
        """Returns a generator that yields raw component data from action rows one by one, as provided by Discord.
        This does not contain all fields of the components due to API limitations.

        .. versionadded:: 2.6

        Returns
        -------
        Generator[:class:`dict`, None, None]
        """
        for action_row in self.data.components:
            yield from action_row["components"]

    @cached_slot_property("_cs_text_values")
    def text_values(self) -> Dict[str, str]:
        """Dict[:class:`str`, :class:`str`]: Returns the text values the user has entered in the modal.
        This is a dict of the form ``{custom_id: value}``.
        """
        text_input_type = ComponentType.text_input.value
        return {
            component["custom_id"]: component.get("value") or ""
            for component in self.walk_raw_components()
            if component.get("type") == text_input_type
        }

    @property
    def custom_id(self) -> str:
        """:class:`str`: The custom ID of the modal."""
        return self.data.custom_id


class ModalInteractionData(Dict[str, Any]):
    """Represents the data of an interaction with a modal.

    .. versionadded:: 2.4

    Attributes
    ----------
    custom_id: :class:`str`
        The custom ID of the modal.
    components: List[:class:`dict`]
        The raw component data of the modal interaction, as provided by Discord.
        This does not contain all fields of the components due to API limitations.

        .. versionadded:: 2.6
    """

    __slots__ = ("custom_id", "components")

    def __init__(self, *, data: ModalInteractionDataPayload) -> None:
        super().__init__(data)
        self.custom_id: str = data["custom_id"]
        # This uses a stripped-down action row TypedDict, as we only receive
        # partial data from the API, generally only containing `type`, `custom_id`,
        # and relevant fields like a select's `values`.
        self.components: List[ModalInteractionActionRowPayload] = data["components"]

    def __repr__(self) -> str:
        return f"<ModalInteractionData custom_id={self.custom_id!r} components={self.components!r}>"
