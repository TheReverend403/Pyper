import json
import logging

import requests
import telebot
from lib import importdir
from lib.command import Command


class Bot:
    def __init__(self, config):
        self._config = config
        self.telegram = telebot.TeleBot(config.get('bot', 'key'))
        telebot.logger.setLevel(logging.WARNING)
        self.logger = logging.getLogger('Pyper')
        self.commands = {}
        self._init_commands()
        self.telegram.set_update_listener(self._handle_messages)

    def _init_commands(self):
        self.logger.info('Loading commands.')
        importdir.do('commands', globals())
        disabled_commands = json.loads(self._config.get('bot', 'disabled_commands')) \
            if self._config.has_option('bot', 'disabled_commands') else []
        for command in Command.__subclasses__():
            if command.name not in disabled_commands:
                self._enable_command(command)
            else:
                del command
        self.logger.info('Enabled commands: [%s].', ', '.join(self.commands.keys()))
        if disabled_commands:
            self.logger.info('Disabled commands: [%s].', ', '.join(disabled_commands))

    def _handle_messages(self, messages):
        for message in messages:
            self.logger.debug(message)
            if message.text.startswith('/'):
                message_text = message.text.strip('/')
                if not message_text:
                    return
                command_split = message_text.split()
                command_name = ''.join(command_split[:1])
                args = command_split[1:]
                if not args:
                    args = []
                for command in self.commands:
                    command = self.commands[command]
                    if command_name == command.name or hasattr(command, 'aliases') and command_name in command.aliases:
                        self.logger.info('Command %s with args [%s] invoked by %s', command.name, ', '.join(args),
                                         message.from_user)
                        command.run(message, args)

    def poll(self):
        try:
            self.telegram.polling(timeout=10)
        except requests.exceptions.ConnectionError as ex:
            self.logger.exception(ex)
            self.telegram.stop_polling()
            self.poll()
        except KeyboardInterrupt:
            self.telegram.stop_polling()

    def _enable_command(self, command):
        if command not in self.commands.values():
            config = dict(self._config.items(command.name)) if self._config.has_section(command.name) else None
            command = command(self, config)
            self.commands[command.name] = command
