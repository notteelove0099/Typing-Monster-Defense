import pygame
import random
import sys
import os

# ==========================================
# 1. ตั้งค่าพื้นฐานของเกม
# ==========================================
pygame.init()
WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Typing Monster Defense (Final Version)")
clock = pygame.time.Clock()

# --- สี ---
BLACK = (20, 20, 20)
WHITE = (255, 255, 255)
GRAY_BOX = (50, 50, 60)
GREEN_TYPED = (100, 255, 100)
YELLOW_TARGET = (255, 255, 100)
RED = (255, 80, 80)
BLUE_MENU = (100, 150, 255)
ORANGE = (255, 165, 0)

# สีปุ่ม
BTN_EASY = (50, 150, 50)
HOVER_EASY = (80, 200, 80)
BTN_MED = (50, 100, 200)
HOVER_MED = (80, 150, 255)
BTN_HARD = (200, 50, 50)
HOVER_HARD = (255, 80, 80)
BTN_PAUSE = (200, 150, 50) 
HOVER_PAUSE = (255, 200, 100)
BTN_HELP = (50, 150, 200)   
HOVER_HELP = (80, 200, 255)
BTN_GRAY = (100, 100, 100)  
HOVER_GRAY = (150, 150, 150)

# --- ฟอนต์ภาษาไทย ---
try:
    font = pygame.font.SysFont("tahoma", 24, bold=True)
    ui_font = pygame.font.SysFont("tahoma", 20, bold=True)
    title_font = pygame.font.SysFont("tahoma", 42, bold=True)
    inst_font = pygame.font.SysFont("tahoma", 24)
except:
    font = pygame.font.SysFont('arial', 24, bold=True)
    ui_font = pygame.font.SysFont('arial', 20)
    title_font = pygame.font.SysFont('arial', 42, bold=True)
    inst_font = pygame.font.SysFont('arial', 24)

# ==========================================
# 2. ระบบดึงคำศัพท์จากไฟล์ (File I/O)
# ==========================================
WORD_LIST = ["python", "project", "coding", "game", "keyboard"] # คำศัพท์สำรอง

def load_words(filename):
    words = []
    try:
        # เช็คว่าเกมรันแบบไฟล์ .exe หรือแบบสคริปต์ปกติ
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable) # ดึง Path ของโฟลเดอร์ที่ .exe วางอยู่
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__)) # ดึง Path ปกติ
            
        file_path = os.path.join(base_dir, filename)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                clean_word = line.strip().lower()
                if clean_word and clean_word.isalpha():
                    words.append(clean_word)
        print(f"[System] สำเร็จ! ดึงคำศัพท์มาได้ {len(words)} คำจาก {file_path}")
        return words
    except FileNotFoundError:
        print(f"[Warning] หาไฟล์ {filename} ไม่เจอ! กำลังใช้คำศัพท์สำรอง")
        return None

# โหลดคำศัพท์ตอนเริ่มเกม
loaded_words = load_words('words.txt')
if loaded_words:
    WORD_LIST = loaded_words

# ==========================================
# 3. ส่วนเตรียม Asset (รูปภาพมอนสเตอร์)
# ==========================================
def create_placeholder_monster(color):
    surf = pygame.Surface((80, 80))
    surf.fill(color)
    pygame.draw.rect(surf, WHITE, (15, 20, 10, 10))
    pygame.draw.rect(surf, WHITE, (55, 20, 10, 10))
    return surf

monster_images = [
    create_placeholder_monster(RED),
    create_placeholder_monster((50, 100, 255)),
    create_placeholder_monster((100, 255, 50)),
]

# ==========================================
# 4. Class ศัตรู
# ==========================================
class Enemy:
    def __init__(self, word, x, speed, image):
        self.word = word
        self.image = image
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.x = x
        self.y = -150
        self.speed = speed
        self.typed_index = 0

    def update(self):
        self.y += self.speed

    def draw(self, surface, is_active):
        surface.blit(self.image, (self.x, self.y))
        box_margin = 5
        box_y = self.y + self.height + 10
        
        typed_str = self.word[:self.typed_index]
        untyped_str = self.word[self.typed_index:]
        
        typed_text_surf = font.render(typed_str, True, GREEN_TYPED)
        untyped_color = YELLOW_TARGET if is_active else WHITE
        untyped_text_surf = font.render(untyped_str, True, untyped_color)
        
        total_text_width = typed_text_surf.get_width() + untyped_text_surf.get_width()
        text_height = typed_text_surf.get_height()

        box_width = total_text_width + (box_margin * 4)
        box_height = text_height + (box_margin * 2)
        box_x = self.x + (self.width / 2) - (box_width / 2)

        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(surface, GRAY_BOX, box_rect, border_radius=8)
        
        if is_active:
            pygame.draw.rect(surface, YELLOW_TARGET, box_rect, width=2, border_radius=8)

        text_start_x = box_x + (box_width - total_text_width) / 2
        text_start_y = box_y + box_margin

        surface.blit(typed_text_surf, (text_start_x, text_start_y))
        surface.blit(untyped_text_surf, (text_start_x + typed_text_surf.get_width(), text_start_y))

# ==========================================
# 5. Game Loop และระบบ State
# ==========================================
def main():
    game_state = "MENU"
    difficulty_settings = {}
    
    enemies = []
    active_enemy = None
    
    score = 0
    player_hp = 3
    combo = 0
    max_combo = 0
    total_keystrokes = 0
    correct_keystrokes = 0
    
    spawn_timer = 0
    spawn_delay = 100
    
    start_ticks = 0
    pause_start_ticks = 0
    time_left = 0
    actual_time_played = 0

    # พิกัดปุ่ม
    btn_width, btn_height = 400, 60
    btn_x = WIDTH // 2 - btn_width // 2
    easy_btn_rect = pygame.Rect(btn_x, HEIGHT // 2 - 20, btn_width, btn_height)
    med_btn_rect = pygame.Rect(btn_x, HEIGHT // 2 + 60, btn_width, btn_height)
    hard_btn_rect = pygame.Rect(btn_x, HEIGHT // 2 + 140, btn_width, btn_height)
    help_btn_rect = pygame.Rect(WIDTH - 180, HEIGHT - 70, 160, 45)
    tut_back_btn_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)
    pause_button_rect = pygame.Rect(20, HEIGHT - 70, 160, 45)
    resume_btn_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 10, 300, 50)
    quit_btn_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 60, 300, 50)

    running = True
    while running:
        # --------------------------------------
        # A. จัดการ Input และ Event
        # --------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if game_state == "MENU":
                        clicked_mode = None
                        if easy_btn_rect.collidepoint(event.pos):
                            difficulty_settings = {"min_speed": 0.2, "max_speed": 0.5, "start_delay": 150, "max_enemies": 5, "time_limit": 300}
                            clicked_mode = True
                        elif med_btn_rect.collidepoint(event.pos):
                            difficulty_settings = {"min_speed": 0.6, "max_speed": 1.2, "start_delay": 100, "max_enemies": 8, "time_limit": 180}
                            clicked_mode = True
                        elif hard_btn_rect.collidepoint(event.pos):
                            difficulty_settings = {"min_speed": 1.0, "max_speed": 2.0, "start_delay": 60, "max_enemies": 12, "time_limit": 120}
                            clicked_mode = True
                        elif help_btn_rect.collidepoint(event.pos):
                            game_state = "HOW_TO_PLAY"

                        if clicked_mode:
                            game_state = "PLAYING"
                            enemies.clear()
                            active_enemy = None
                            score = 0
                            player_hp = 3
                            combo = 0
                            max_combo = 0
                            total_keystrokes = 0
                            correct_keystrokes = 0
                            spawn_timer = 0
                            spawn_delay = difficulty_settings["start_delay"]
                            start_ticks = pygame.time.get_ticks()

                    elif game_state == "PLAYING":
                        if pause_button_rect.collidepoint(event.pos):
                            game_state = "PAUSED"
                            pause_start_ticks = pygame.time.get_ticks()

                    elif game_state == "PAUSED":
                        if resume_btn_rect.collidepoint(event.pos):
                            game_state = "PLAYING"
                            pause_duration = pygame.time.get_ticks() - pause_start_ticks
                            start_ticks += pause_duration 
                        elif quit_btn_rect.collidepoint(event.pos):
                            game_state = "MENU"
                            
                    elif game_state == "HOW_TO_PLAY":
                        if tut_back_btn_rect.collidepoint(event.pos):
                            game_state = "MENU"

            elif event.type == pygame.KEYDOWN:
                char_pressed = event.unicode.lower()

                if game_state == "MENU":
                    clicked_mode = None
                    if char_pressed == '1': 
                        difficulty_settings = {"min_speed": 0.2, "max_speed": 0.5, "start_delay": 150, "max_enemies": 5, "time_limit": 300}
                        clicked_mode = True
                    elif char_pressed == '2': 
                        difficulty_settings = {"min_speed": 0.6, "max_speed": 1.2, "start_delay": 100, "max_enemies": 8, "time_limit": 180}
                        clicked_mode = True
                    elif char_pressed == '3': 
                        difficulty_settings = {"min_speed": 1.0, "max_speed": 2.0, "start_delay": 60, "max_enemies": 12, "time_limit": 120}
                        clicked_mode = True
                        
                    if clicked_mode:
                        game_state = "PLAYING"
                        enemies.clear()
                        active_enemy = None
                        score = 0
                        player_hp = 3
                        combo = 0
                        max_combo = 0
                        total_keystrokes = 0
                        correct_keystrokes = 0
                        spawn_timer = 0
                        spawn_delay = difficulty_settings["start_delay"]
                        start_ticks = pygame.time.get_ticks()

                elif game_state == "PLAYING":
                    if event.key == pygame.K_ESCAPE:
                        game_state = "PAUSED"
                        pause_start_ticks = pygame.time.get_ticks()
                        continue
                    
                    if not char_pressed.isalpha():
                        continue
                        
                    total_keystrokes += 1 

                    if active_enemy is not None:
                        expected_char = active_enemy.word[active_enemy.typed_index]
                        if char_pressed == expected_char:
                            correct_keystrokes += 1
                            combo += 1
                            if combo > max_combo: max_combo = combo
                                
                            active_enemy.typed_index += 1
                            if active_enemy.typed_index == len(active_enemy.word):
                                multiplier = 1 + (combo // 10)
                                score += (10 * multiplier)
                                enemies.remove(active_enemy)
                                active_enemy = None
                        else:
                            combo = 0
                    else:
                        found_target = False
                        for enemy in enemies:
                            if enemy.word.startswith(char_pressed):
                                active_enemy = enemy
                                active_enemy.typed_index += 1
                                correct_keystrokes += 1
                                combo += 1
                                if combo > max_combo: max_combo = combo
                                found_target = True
                                break
                        
                        if not found_target:
                            combo = 0
                
                elif game_state == "PAUSED":
                    if event.key == pygame.K_ESCAPE or char_pressed == 'r':
                        game_state = "PLAYING"
                        pause_duration = pygame.time.get_ticks() - pause_start_ticks
                        start_ticks += pause_duration 
                    elif char_pressed == 'q':
                        game_state = "MENU"

                elif game_state == "GAME_OVER":
                    if char_pressed == 'r': 
                        game_state = "MENU"
                        
                elif game_state == "HOW_TO_PLAY":
                    if event.key == pygame.K_ESCAPE:
                        game_state = "MENU"

        # --------------------------------------
        # B. อัปเดตข้อมูล (เฉพาะตอนเล่น)
        # --------------------------------------
        if game_state == "PLAYING":
            seconds_passed = (pygame.time.get_ticks() - start_ticks) // 1000
            time_left = difficulty_settings["time_limit"] - seconds_passed
            
            if time_left <= 0:
                time_left = 0
                actual_time_played = difficulty_settings["time_limit"] 
                game_state = "GAME_OVER" 
                
            minutes = time_left // 60
            seconds = time_left % 60
            time_str = f"{minutes:02d}:{seconds:02d}"

            spawn_timer += 1
            if spawn_timer >= spawn_delay:
                if len(enemies) < difficulty_settings["max_enemies"]:
                    new_word = random.choice(WORD_LIST)
                    random_x = random.randint(50, WIDTH - 150)
                    min_s = difficulty_settings["min_speed"]
                    max_s = difficulty_settings["max_speed"]
                    random_speed = random.uniform(min_s, max_s)
                    random_image = random.choice(monster_images)
                    enemies.append(Enemy(new_word, random_x, random_speed, random_image))
                    spawn_timer = 0
                    spawn_delay = max(50, spawn_delay - 0.5) 
                else:
                    spawn_timer = spawn_delay

            for enemy in enemies[:]:
                enemy.update()
                if enemy.y > HEIGHT:
                    if enemy == active_enemy:
                        active_enemy = None
                    enemies.remove(enemy)
                    
                    player_hp -= 1
                    combo = 0 
                    
                    if player_hp <= 0:
                        actual_time_played = seconds_passed
                        game_state = "GAME_OVER"

        # --------------------------------------
        # C. วาดหน้าจอ
        # --------------------------------------
        screen.fill(BLACK)
        mouse_pos = pygame.mouse.get_pos()

        if game_state == "MENU":
            title_text = title_font.render("TYPING MONSTER DEFENSE", True, WHITE)
            subtitle_text = ui_font.render("Select Difficulty to Start", True, YELLOW_TARGET)
            screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//4 - 40))
            screen.blit(subtitle_text, (WIDTH//2 - subtitle_text.get_width()//2, HEIGHT//4 + 30))

            buttons = [
                (easy_btn_rect, BTN_EASY, HOVER_EASY, "[1] EASY - 5 Mins", WHITE),
                (med_btn_rect, BTN_MED, HOVER_MED, "[2] NORMAL - 3 Mins", WHITE),
                (hard_btn_rect, BTN_HARD, HOVER_HARD, "[3] HARD - 2 Mins", WHITE),
                (help_btn_rect, BTN_HELP, HOVER_HELP, "? วิธีเล่น", BLACK)
            ]

            for rect, color, hover_color, text, text_color in buttons:
                if rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, hover_color, rect, border_radius=10)
                else:
                    pygame.draw.rect(screen, color, rect, border_radius=10)
                
                btn_text = ui_font.render(text, True, text_color)
                screen.blit(btn_text, (rect.centerx - btn_text.get_width()//2, rect.centery - btn_text.get_height()//2))

        elif game_state == "HOW_TO_PLAY":
            help_title = title_font.render("วิธีเล่น (HOW TO PLAY)", True, YELLOW_TARGET)
            screen.blit(help_title, (WIDTH//2 - help_title.get_width()//2, 80))

            instructions = [
                "1. พิมพ์ตัวอักษรให้ตรงกับคำบนตัวมอนสเตอร์เพื่อทำลายพวกมัน",
                "2. ตัวอักษรแรกที่คุณพิมพ์ จะเป็นการ 'ล็อกเป้าหมาย' (ขึ้นกรอบสีเหลือง)",
                "3. การพิมพ์ถูกต่อเนื่องจะเพิ่ม COMBO ทำให้ได้คะแนนคูณ 2, คูณ 3!",
                "4. ถ้ามอนสเตอร์หลุดจอ 1 ตัว จะเสียหัวใจ 1 ดวง (มีทั้งหมด 3 ดวง)",
                "5. พยายามทำความแม่นยำและเอาตัวรอดให้ได้นานที่สุด!"
            ]
            
            for i, text in enumerate(instructions):
                inst_text = inst_font.render(text, True, WHITE)
                screen.blit(inst_text, (80, 200 + (i * 65)))

            if tut_back_btn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, HOVER_GRAY, tut_back_btn_rect, border_radius=10)
            else:
                pygame.draw.rect(screen, BTN_GRAY, tut_back_btn_rect, border_radius=10)
            
            back_text = font.render("< กลับ (Back)", True, BLACK)
            screen.blit(back_text, (tut_back_btn_rect.centerx - back_text.get_width()//2, tut_back_btn_rect.centery - back_text.get_height()//2))

        elif game_state == "PLAYING" or game_state == "PAUSED":
            
            # --- แก้ไข Z-Index ตรงนี้ ---
            # 1. วาดมอนสเตอร์ที่ยังไม่โดนล็อกเป้าไว้เป็นฉากหลังก่อน
            for enemy in enemies:
                if enemy != active_enemy:
                    enemy.draw(screen, False)
            
            # 2. วาดมอนสเตอร์เป้าหมายหลักทีหลัง เพื่อให้อยู่ข้างหน้าสุดเสมอ
            if active_enemy is not None:
                active_enemy.draw(screen, True)
            # ---------------------------

            score_text = ui_font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (20, 20))
            
            if combo > 1:
                multiplier = 1 + (combo // 10)
                combo_str = f"Combo: {combo} (x{multiplier})"
                combo_text = font.render(combo_str, True, ORANGE)
                screen.blit(combo_text, (20, 50))

            time_color = RED if time_left <= 30 else GREEN_TYPED 
            timer_text = ui_font.render(f"Time: {time_str}", True, time_color)
            screen.blit(timer_text, (WIDTH - 150, 20))
            
            hp_text = ui_font.render(f"HP: {'♥ ' * player_hp}", True, RED)
            screen.blit(hp_text, (WIDTH - 150, 50))

            if game_state == "PLAYING":
                if pause_button_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, HOVER_PAUSE, pause_button_rect, border_radius=8)
                else:
                    pygame.draw.rect(screen, BTN_PAUSE, pause_button_rect, border_radius=8)
                
                btn_text = ui_font.render("|| หยุด (Pause)", True, BLACK)
                screen.blit(btn_text, (pause_button_rect.x + 10, pause_button_rect.y + 8))

            if game_state == "PAUSED":
                overlay = pygame.Surface((WIDTH, HEIGHT))
                overlay.set_alpha(180) 
                overlay.fill((0, 0, 0))
                screen.blit(overlay, (0, 0))

                pause_title = title_font.render("หยุดเกมชั่วคราว", True, YELLOW_TARGET)
                screen.blit(pause_title, (WIDTH//2 - pause_title.get_width()//2, HEIGHT//3 - 30))

                if resume_btn_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, HOVER_EASY, resume_btn_rect, border_radius=10)
                else:
                    pygame.draw.rect(screen, BTN_EASY, resume_btn_rect, border_radius=10)
                res_text = font.render("เล่นต่อ (Resume)", True, WHITE)
                screen.blit(res_text, (resume_btn_rect.centerx - res_text.get_width()//2, resume_btn_rect.centery - res_text.get_height()//2))

                if quit_btn_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, HOVER_HARD, quit_btn_rect, border_radius=10)
                else:
                    pygame.draw.rect(screen, BTN_HARD, quit_btn_rect, border_radius=10)
                quit_text = font.render("ออกไปหน้าหลัก", True, WHITE)
                screen.blit(quit_text, (quit_btn_rect.centerx - quit_text.get_width()//2, quit_btn_rect.centery - quit_text.get_height()//2))

        elif game_state == "GAME_OVER":
            accuracy = 0
            if total_keystrokes > 0:
                accuracy = (correct_keystrokes / total_keystrokes) * 100
                
            played_minutes = actual_time_played / 60.0
            wpm = 0
            if played_minutes > 0:
                wpm = (correct_keystrokes / 5) / played_minutes

            go_title = title_font.render("GAME OVER!" if player_hp <= 0 else "TIME'S UP!", True, RED if player_hp <= 0 else YELLOW_TARGET)
            go_score = title_font.render(f"Final Score: {score}", True, WHITE)
            
            stat_combo = font.render(f"Max Combo: {max_combo}", True, ORANGE)
            stat_acc = font.render(f"Accuracy: {accuracy:.1f}%", True, GREEN_TYPED)
            stat_wpm = font.render(f"Typing Speed: {int(wpm)} WPM", True, BLUE_MENU)
            
            restart_text = ui_font.render("Press 'R' to return to Menu", True, GRAY_BOX)
            
            screen.blit(go_title, (WIDTH//2 - go_title.get_width()//2, 100))
            screen.blit(go_score, (WIDTH//2 - go_score.get_width()//2, 180))
            
            screen.blit(stat_combo, (WIDTH//2 - stat_combo.get_width()//2, 280))
            screen.blit(stat_acc, (WIDTH//2 - stat_acc.get_width()//2, 330))
            screen.blit(stat_wpm, (WIDTH//2 - stat_wpm.get_width()//2, 380))
            
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT - 100))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()