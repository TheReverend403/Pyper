from imdbpie import Imdb

from lib.command import Command
from lib.utils import telegram_escape


class ImdbCommand(Command):
    name = 'imdb'
    aliases = ['movie']
    description = 'Searches IMDB for movie titles.'

    def __init__(self, bot, config):
        super().__init__(bot, config)
        self._imdb = Imdb(cache=True, exclude_episodes=True)

    def run(self, message, args):
        if not args:
            self.reply(message, 'Please supply some search terms!')
            return

        self.bot.telegram.send_chat_action(message.chat.id, 'typing')
        results = self._imdb.search_for_title(' '.join(args))
        if not results:
            self.reply(message, 'No results found!')
            return

        result = self._imdb.get_title_by_id(results[0]['imdb_id'])
        reply = '<b>URL:</b> http://www.imdb.com/title/{0}\n'.format(telegram_escape(result.imdb_id))
        reply += '<b>Title:</b> {0}\n'.format(telegram_escape(result.title))
        reply += '<b>Year:</b> {0}\n'.format(result.year)
        reply += '<b>Genre:</b> {0}\n'.format(telegram_escape(', '.join(result.genres[:3])))
        reply += '<b>Rating:</b> {0}\n'.format(result.rating)
        runtime, _ = divmod(result.runtime, 60)
        reply += '<b>Runtime:</b> {0} minutes\n'.format(runtime)
        reply += '<b>Certification:</b> {0}\n'.format(result.certification)
        reply += '<b>Cast:</b> {0}\n'.format(
            telegram_escape(', '.join([person.name for person in result.cast_summary[:5]])))
        reply += '<b>Director(s):</b> {0}\n\n'.format(
            telegram_escape(', '.join([person.name for person in result.directors_summary[:5]])))
        reply += telegram_escape(result.plots[0])

        self.reply(message, reply, parse_mode='HTML')
