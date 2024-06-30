import telebot
from telebot import types


token = '6528345957:AAGIIy4Tu9eVpJvGTtrLcJlqu46pjXW-idg'
bot = telebot.TeleBot(token)

max_errors = 6

class UserState:
    def __init__(self, target_word=None, word_mask=None, incorrect_attempts=0, last_message_id=None):
        self.target_word = target_word
        self.word_mask = word_mask
        self.incorrect_attempts = incorrect_attempts
        self.last_message_id = last_message_id

user_states = {}


start_game_button = types.KeyboardButton("Почати гру")
keyboard_markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
keyboard_markup.add(start_game_button)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    if user_states.get(user_id):
        handle_guess(message)
    else:
        if message.text == "Почати гру":
            bot.send_message(message.chat.id, "Введи слово до 8 букв:", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, process_word_input)
        else:
            bot.send_message(message.chat.id, "Натисніть кнопку 'Почати гру', щоб загадати слово.", reply_markup=keyboard_markup)

def process_word_input(message):
    user_id = message.from_user.id
    word = message.text.strip().lower()

    if len(word) <= 8:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except telebot.apihelper.ApiException as e:
            print(f"Error deleting message: {e}")

        user_states[user_id] = UserState(target_word=word, word_mask=['*' if letter.isalpha() else letter for letter in word])
        new_message = bot.send_message(message.chat.id, f"Користувач ввів слово: {''.join(user_states[user_id].word_mask)}. Можете почати загадувати буква.")
        user_states[user_id].last_message_id = new_message.message_id
        bot.register_next_step_handler(new_message, handle_guess)
    else:
        bot.send_message(message.chat.id, "Слово має містити 8 або менше літер.")
        bot.register_next_step_handler(message, process_word_input)
@bot.message_handler(func=lambda message: True)
def handle_guess(message):
    user_id = message.from_user.id

    if not user_states.get(user_id):
        bot.reply_to(message, "Для початку введіть команду /start")
        return

   
    
    if message.text == '/end':
        bot.send_message(message.chat.id, "Гра завершена.", reply_markup=keyboard_markup)
        del user_states[user_id]
        return
    
    guessed_letter = message.text.strip().lower()
    if len(guessed_letter) != 1 or not guessed_letter.isalpha():
        bot.reply_to(message, "Введіть лише одну букву!.")
        return

    if guessed_letter in user_states[user_id].word_mask:
        bot.reply_to(message, f"Ця буква вже відгадана. Спробуйте іншу")
        return

    if guessed_letter in user_states[user_id].target_word:
        bot.reply_to(message, f"Непогано! Буква '{guessed_letter}' є в слові.")
        update_word_mask(user_id, guessed_letter)
        bot.send_message(message.chat.id, f"Слово: {''.join(user_states[user_id].word_mask)}")
        if all(letter.isalpha() for letter in user_states[user_id].word_mask):
            bot.send_message(message.chat.id, f"Вітаю. Ви відгадали слово '{user_states[user_id].target_word}'. Гра завершена.")
            del user_states[user_id]
    else:
        user_states[user_id].incorrect_attempts += 1
        errors = user_states[user_id].incorrect_attempts
        bot.reply_to(message, f"Букви '{guessed_letter}' немає в слові. Помилок: {errors} з {max_errors}.")

        if errors <= max_errors:
            image_path = f"image{errors + 1}.png"
            with open(image_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo)

        if errors >= max_errors:
            bot.send_message(message.chat.id, f"Гра завершена. Слово було '{user_states[user_id].target_word}'")
            del user_states[user_id]

def update_word_mask(user_id, guessed_letter):
    user_states[user_id].word_mask = [letter if user_states[user_id].target_word[idx] == guessed_letter else mask for idx, (letter, mask) in enumerate(zip(user_states[user_id].target_word, user_states[user_id].word_mask))]

bot.polling(none_stop=True)