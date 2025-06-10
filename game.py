import pygame
import sys
import random

# Pygame 초기화
pygame.init()

# 게임 상수 (모바일 화면비로 변경)
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 800
FPS = 60

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 200, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)

# 물리 상수 (밸런스 조정)
GRAVITY = 0.9          # 중력 조정
JUMP_STRENGTH = -20     # 점프력 증가 (더 높이 점프 가능)
ACCELERATION = 1.5      # 가속력 대폭 증가 (더 빠른 좌우 이동)
FRICTION = 0.85         # 마찰력 조정
MAX_SPEED = 16          # 최대 속도 대폭 증가

# 카메라 상수
CAMERA_DEADZONE = 200   # 데드존 크기 (점프력에 맞게 조정)
CAMERA_SMOOTH = 0.08    # 카메라 부드러움 (0.01=매우부드러움, 0.2=빠름)

# 게임 상태
MENU = 0
PLAYING = 1
GAME_OVER = 2

class Camera:
    """데드존 카메라 클래스"""
    def __init__(self):
        self.y = 0
        self.target_y = 0
    
    def update(self, player_y):
        """데드존 방식으로 카메라 업데이트"""
        # 화면 중앙 기준 플레이어 위치
        player_screen_y = player_y - self.y
        screen_center = SCREEN_HEIGHT // 2
        
        # 데드존 범위 (화면 중앙 ± CAMERA_DEADZONE)
        deadzone_top = screen_center - CAMERA_DEADZONE // 2
        deadzone_bottom = screen_center + CAMERA_DEADZONE // 2
        
        # 데드존을 벗어나면 카메라 이동
        if player_screen_y < deadzone_top:
            self.target_y = player_y - deadzone_top
        elif player_screen_y > deadzone_bottom:
            self.target_y = player_y - deadzone_bottom
        
        # 부드럽게 이동
        self.y += (self.target_y - self.y) * CAMERA_SMOOTH

class Player:
    """플레이어 클래스"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 25
        self.height = 25
        self.vel_x = 0
        self.vel_y = 0
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def update(self):
        # 수평 이동 (관성 적용)
        self.x += self.vel_x
        self.vel_x *= FRICTION
        
        # 화면 경계 처리
        if self.x < 0:
            self.x = 0
            self.vel_x = 0
        elif self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
            self.vel_x = 0
        
        # 중력 적용
        self.vel_y += GRAVITY
        self.y += self.vel_y
        
        # rect 위치 업데이트
        self.rect.x = self.x
        self.rect.y = self.y
    
    def move_left(self):
        self.vel_x -= ACCELERATION
        if self.vel_x < -MAX_SPEED:
            self.vel_x = -MAX_SPEED
    
    def move_right(self):
        self.vel_x += ACCELERATION
        if self.vel_x > MAX_SPEED:
            self.vel_x = MAX_SPEED
    
    def jump(self):
        self.vel_y = JUMP_STRENGTH
    
    def draw(self, screen, camera_y):
        """카메라 오프셋 적용하여 그리기"""
        draw_y = self.y - camera_y
        pygame.draw.rect(screen, BLUE, (self.x, draw_y, self.width, self.height))
        # 작은 눈 그리기
        pygame.draw.circle(screen, WHITE, (int(self.x + 7), int(draw_y + 7)), 2)
        pygame.draw.circle(screen, WHITE, (int(self.x + 18), int(draw_y + 7)), 2)

class Platform:
    """발판 클래스"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 70
        self.height = 15
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def draw(self, screen, camera_y):
        """카메라 오프셋 적용하여 그리기"""
        draw_y = self.y - camera_y
        # 화면 범위 내에 있을 때만 그리기 (최적화)
        if -50 < draw_y < SCREEN_HEIGHT + 50:
            pygame.draw.rect(screen, GREEN, (self.x, draw_y, self.width, self.height))
            pygame.draw.rect(screen, BLACK, (self.x, draw_y, self.width, self.height), 1)

class Game:
    """메인 게임 클래스"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("")
        self.clock = pygame.time.Clock()
        
        self.state = MENU
        self.running = True
        
        # 폰트 (한 번만 생성)
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        self.reset_game()
    
    def reset_game(self):
        """게임 리셋"""
        self.player = Player(SCREEN_WIDTH // 2 - 12, SCREEN_HEIGHT - 150)
        self.camera = Camera()
        self.platforms = []
        self.score = 0
        self.platform_timer = 0
        self.platform_spawn_interval = 25
        self.create_initial_platforms()
    
    def create_initial_platforms(self):
        """게임 시작용 발판들 생성 (밀도 조정으로 밸런스 개선)"""
        # 시작 발판
        self.platforms.append(Platform(SCREEN_WIDTH // 2 - 35, SCREEN_HEIGHT - 80))
        
        # 초기 발판들 생성 (개수와 밀도 대폭 축소)
        for i in range(6):  # 9개 → 6개로 축소
            # 각 높이마다 1개씩만 생성 (기존 1-2개에서 1개로 고정)
            x = random.randint(0, SCREEN_WIDTH - 70)
            y = SCREEN_HEIGHT - 200 - (i * 100)  # 간격 늘림 (80 → 100)
            self.platforms.append(Platform(x, y))
    
    def spawn_platforms(self):
        """발판들 생성 (개수 대폭 축소, 점프력 증가로 밸런스)"""
        platform_count = random.randint(2, 3)  # 3-5개 → 2-3개로 축소
        
        for _ in range(platform_count):
            # 최대 10번 시도해서 겹치지 않는 위치 찾기
            for attempt in range(10):
                x = random.randint(0, SCREEN_WIDTH - 70)
                y = random.randint(int(self.camera.y - 350), int(self.camera.y - 80))  # 범위 조정
                
                # 화면 근처 발판들과 겹치지 않는지 체크
                is_overlapping = False
                for platform in self.platforms:
                    # 카메라 근처 발판만 체크 (성능 최적화)
                    if abs(platform.y - self.camera.y) < 400:
                        # 발판 크기를 고려한 겹침 체크 (간격 더 늘림)
                        if (abs(platform.x - x) < 90 and  # 수평 간격 증가 (80 → 90)
                            abs(platform.y - y) < 60):   # 수직 간격 증가 (50 → 60)
                            is_overlapping = True
                            break
                
                # 겹치지 않으면 발판 생성하고 다음으로
                if not is_overlapping:
                    self.platforms.append(Platform(x, y))
                    break
        
        # 수평 라인 발판들 생성 (확률과 개수 대폭 축소)
        if random.randint(1, 6) == 1:  # 25% → 16% 확률로 축소
            y_line = random.randint(int(self.camera.y - 250), int(self.camera.y - 120))
            
            # 해당 높이에 이미 발판이 있는지 체크
            line_conflict = any(abs(p.y - y_line) < 40 for p in self.platforms 
                              if abs(p.y - self.camera.y) < 400)
            
            if not line_conflict:
                # 수평 라인 발판 1개만 생성 (기존 2개에서 1개로 축소)
                x = SCREEN_WIDTH // 2 - 35 + random.randint(-80, 80)
                if 0 <= x <= SCREEN_WIDTH - 70:
                    # 기존 발판들과 겹치지 않는지 확인
                    is_safe = True
                    for platform in self.platforms:
                        if (abs(platform.x - x) < 90 and 
                            abs(platform.y - y_line) < 60):
                            is_safe = False
                            break
                    
                    if is_safe:
                        self.platforms.append(Platform(x, y_line))
    
    def handle_events(self):
        """이벤트 처리"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    if self.state == MENU:
                        self.state = PLAYING
                        self.reset_game()
                    elif self.state == GAME_OVER:
                        self.state = PLAYING
                        self.reset_game()
            elif event.type == pygame.MOUSEBUTTONDOWN and self.state != PLAYING:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                button_rect = pygame.Rect(SCREEN_WIDTH//2 - 80, 
                                        SCREEN_HEIGHT//2 + (0 if self.state == MENU else 50), 
                                        160, 50)
                if button_rect.collidepoint(mouse_x, mouse_y):
                    self.state = PLAYING
                    self.reset_game()
    
    def handle_input(self):
        """연속 키 입력 처리"""
        if self.state == PLAYING:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.player.move_left()
            if keys[pygame.K_RIGHT]:
                self.player.move_right()
    
    def check_collisions(self):
        """충돌 감지 - 가까운 발판만 체크 (최적화)"""
        for platform in self.platforms[:]:
            # 플레이어와 가까운 발판만 체크
            if abs(platform.y - self.player.y) < 100:
                if self.player.rect.colliderect(platform.rect):
                    if (self.player.vel_y > 0 and self.player.y < platform.y):
                        self.player.y = platform.y - self.player.height
                        self.player.jump()
                        self.score += 1
                        self.platforms.remove(platform)
                        break
    
    def update(self):
        """게임 로직 업데이트"""
        if self.state == PLAYING:
            self.player.update()
            self.camera.update(self.player.y)  # 카메라 업데이트
            
            # 게임 오버 체크 (카메라 기준으로 수정)
            if self.player.y > self.camera.y + SCREEN_HEIGHT + 200:
                self.state = GAME_OVER
            
            self.check_collisions()
            
            # 발판 생성
            self.platform_timer += 1
            if self.platform_timer >= self.platform_spawn_interval:
                self.spawn_platforms()
                self.platform_timer = 0
            
            # 데드존 아래로 벗어난 발판 삭제 (최적화)
            deadzone_bottom = self.camera.y + SCREEN_HEIGHT // 2 + CAMERA_DEADZONE // 2
            self.platforms = [p for p in self.platforms 
                            if p.y < deadzone_bottom + SCREEN_HEIGHT // 2]
    
    def draw_menu(self):
        """메뉴 화면"""
        self.screen.fill(LIGHT_BLUE)
        
        title_text = self.font_large.render("JUMP GAME", True, BLACK)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(title_text, title_rect)
        
        button_rect = pygame.Rect(SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2, 160, 50)
        pygame.draw.rect(self.screen, GREEN, button_rect)
        pygame.draw.rect(self.screen, BLACK, button_rect, 2)
        
        button_text = self.font_medium.render("Game Start", True, BLACK)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        self.screen.blit(button_text, button_text_rect)
        
        control_text = self.font_small.render("Arrow keys: move, Spacebar: start", True, BLACK)
        control_rect = control_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100))
        self.screen.blit(control_text, control_rect)
    
    def draw_game(self):
        """게임 화면"""
        self.screen.fill(WHITE)
        
        # 카메라 오프셋 적용하여 게임 객체들 그리기
        self.player.draw(self.screen, self.camera.y)
        for platform in self.platforms:
            platform.draw(self.screen, self.camera.y)
        
        # UI는 고정 위치 (점수)
        score_text = self.font_medium.render(f"Score : {self.score}", True, BLACK)
        self.screen.blit(score_text, (10, 10))
    
    def draw_game_over(self):
        """게임 오버 화면"""
        self.screen.fill(WHITE)
        
        game_over_text = self.font_large.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(game_over_text, game_over_rect)
        
        final_score_text = self.font_medium.render(f"Final Score: {self.score}", True, BLACK)
        final_score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(final_score_text, final_score_rect)
        
        button_rect = pygame.Rect(SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 + 50, 160, 50)
        pygame.draw.rect(self.screen, GREEN, button_rect)
        pygame.draw.rect(self.screen, BLACK, button_rect, 2)
        
        button_text = self.font_medium.render("Restart", True, BLACK)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        self.screen.blit(button_text, button_text_rect)
        
        instruction_text = self.font_small.render("Press any key to restart", True, GRAY)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 130))
        self.screen.blit(instruction_text, instruction_rect)
    
    def draw(self):
        """화면 그리기"""
        if self.state == MENU:
            self.draw_menu()
        elif self.state == PLAYING:
            self.draw_game()
        elif self.state == GAME_OVER:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def run(self):
        """메인 게임 루프"""
        print("=== JUMP GAME ===")
        print("Press spacebar to start")
        
        while self.running:
            self.handle_events()
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

# 게임 실행
if __name__ == "__main__":
    game = Game()
    game.run()
