import disnake
from disnake.ext import commands, tasks
import datetime

# --- НАСТРОЙКИ ----
TOKEN = "MTQ3MTQ5OTYxNDA3MzkxMzQwNA.GaWSEi.QEd-kMjfsN7tc-kJSWM67ViWHy0yH9a46zqs_w"
GUILD_ID = 1471140197256134787
LOG_CHANNEL_ID = 1471542780068102329
CONTROL_CHANNEL_NAME = "🕹️упр-войсами"
CREATE_VOICE_NAME = "➕ Создать войс"

bot = commands.InteractionBot(intents=disnake.Intents.all())
private_rooms = {}  # {id_канала: id_владельца}


# --- ТАЙМЕР-ПИНГ (ДЛЯ ХОСТИНГА) ---
@tasks.loop(minutes=10)
async def keep_alive_ping():
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        await channel.send(f"🤖 Пинг системы: {now} | Статус: OK", delete_after=5)
    else:
        print(f"Ошибка: Не удалось найти лог-канал с ID {LOG_CHANNEL_ID}")


# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
class VoiceControlView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def check_owner(self, inter: disnake.MessageInteraction):
        if not inter.author.voice or inter.author.voice.channel.id not in private_rooms:
            await inter.send("❌ Вы должны находиться в своей приватной комнате!", ephemeral=True)
            return False
        if private_rooms[inter.author.voice.channel.id] != inter.author.id:
            await inter.send("❌ Вы не являетесь владельцем этой комнаты!", ephemeral=True)
            return False
        return True

    @disnake.ui.button(emoji="👑", style=disnake.ButtonStyle.secondary, custom_id="v_transfer")
    async def transfer(self, _, inter: disnake.MessageInteraction):
        if await self.check_owner(inter):
            await inter.send("Передача прав временно доступна только через администрацию.", ephemeral=True)

    @disnake.ui.button(emoji="👤", style=disnake.ButtonStyle.secondary, custom_id="v_access")
    async def access(self, _, inter: disnake.MessageInteraction):
        if await self.check_owner(inter):
            ch = inter.author.voice.channel
            ov = ch.overwrites_for(inter.guild.default_role)
            ov.connect = not ov.connect
            await ch.set_permissions(inter.guild.default_role, overwrite=ov)
            await inter.send(f"✅ Доступ {'открыт' if ov.connect else 'закрыт'}", ephemeral=True)

    @disnake.ui.button(emoji="👥", style=disnake.ButtonStyle.secondary, custom_id="v_limit")
    async def limit(self, _, inter: disnake.MessageInteraction):
        if await self.check_owner(inter):
            await inter.response.send_modal(
                title="Лимит участников",
                custom_id="modal_limit",
                components=[disnake.ui.TextInput(label="Число (0 - убрать лимит)", custom_id="lim")]
            )

    @disnake.ui.button(emoji="🔒", style=disnake.ButtonStyle.secondary, custom_id="v_lock")
    async def lock(self, _, inter: disnake.MessageInteraction):
        if await self.check_owner(inter):
            ch = inter.author.voice.channel
            ov = ch.overwrites_for(inter.guild.default_role)
            ov.connect = not ov.connect
            await ch.set_permissions(inter.guild.default_role, overwrite=ov)
            await inter.send(f"✅ Статус комнаты: {'Открыта' if ov.connect else 'Закрыта'}", ephemeral=True)

    @disnake.ui.button(emoji="📝", style=disnake.ButtonStyle.secondary, custom_id="v_rename")
    async def rename(self, _, inter: disnake.MessageInteraction):
        if inter.author.voice and inter.author.voice.channel.id in private_rooms:
            await inter.response.send_modal(
                title="Смена названия",
                custom_id="modal_rename",
                components=[disnake.ui.TextInput(label="Новое имя", custom_id="name")]
            )
        else:
            await inter.send("❌ Зайдите в приватный войс!", ephemeral=True)

    @disnake.ui.button(emoji="👁️", style=disnake.ButtonStyle.secondary, custom_id="v_hide")
    async def hide(self, _, inter: disnake.MessageInteraction):
        if await self.check_owner(inter):
            ch = inter.author.voice.channel
            ov = ch.overwrites_for(inter.guild.default_role)
            ov.view_channel = not ov.view_channel
            await ch.set_permissions(inter.guild.default_role, overwrite=ov)
            await inter.send(f"✅ Видимость: {'Видна всем' if ov.view_channel else 'Скрыта'}", ephemeral=True)

    @disnake.ui.button(emoji="🚪", style=disnake.ButtonStyle.secondary, custom_id="v_kick")
    async def kick(self, _, inter: disnake.MessageInteraction):
        if await self.check_owner(inter):
            await inter.send("Функция кика участников находится в разработке.", ephemeral=True)

    @disnake.ui.button(emoji="🎙️", style=disnake.ButtonStyle.secondary, custom_id="v_speak")
    async def speak(self, _, inter: disnake.MessageInteraction):
        if await self.check_owner(inter):
            ch = inter.author.voice.channel
            ov = ch.overwrites_for(inter.guild.default_role)
            ov.speak = not ov.speak
            await ch.set_permissions(inter.guild.default_role, overwrite=ov)
            await inter.send(f"✅ Право говорить: {'Выдано' if ov.speak else 'Забрано'}", ephemeral=True)

async def sync_panel():
    guild = bot.get_guild(GUILD_ID)
    if not guild: return
    channel = disnake.utils.get(guild.text_channels, name=CONTROL_CHANNEL_NAME)
    if channel:
        await channel.purge(limit=10, check=lambda m: m.author == bot.user)
        embed = disnake.Embed(
            title="⚙️ Приватные комнаты",
            description=(
                "Измените конфигурацию вашей комнаты с помощью панели управления.\n"
                "👑 — назначить нового создателя комнаты\n"
                "👤 — ограничить/выдать доступ к комнате\n"
                "👥 — задать новый лимит участников\n"
                "🔒 — закрыть/открыть комнату\n"
                "📝 — изменить название комнаты\n"
                "👁️ — скрыть/открыть комнату\n"
                "🚪 — выгнать участника из комнаты\n"
                "🎙️ — ограничить/выдать право говорить"
            ),
            color=0x2b2d31
        )
        await channel.send(embed=embed, view=VoiceControlView())
@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен и готов к работе!")
    bot.add_view(VoiceControlView())
    if not keep_alive_ping.is_running():
        keep_alive_ping.start()
    await sync_panel()


@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.name == CREATE_VOICE_NAME:
        try:
            new_ch = await member.guild.create_voice_channel(
                name=f"🏮 {member.display_name}",
                category=after.channel.category
            )
            await member.move_to(new_ch)
            private_rooms[new_ch.id] = member.id
        except Exception as e:
            print(f"Ошибка при создании: {e}")
    if before.channel and before.channel.id in private_rooms:
        if len(before.channel.members) == 0:
            try:
                await before.channel.delete()
                del private_rooms[before.channel.id]
            except:
                pass


@bot.event
async def on_modal_submit(inter: disnake.ModalInteraction):
    if inter.custom_id == "modal_rename":
        name = inter.text_values["name"]
        await inter.author.voice.channel.edit(name=name)
        await inter.send(f"✅ Название изменено на **{name}**", ephemeral=True)

    if inter.custom_id == "modal_limit":
        try:
            val = int(inter.text_values["lim"])
            await inter.author.voice.channel.edit(user_limit=val)
            await inter.send(f"✅ Лимит изменен на **{val}**", ephemeral=True)
        except:
            await inter.send("❌ Введите число!", ephemeral=True)


bot.run(TOKEN)