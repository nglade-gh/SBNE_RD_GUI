import pygame

# Fonction permettant d'afficher le bandeau en haut de l'écran avec les informations de la simulation
def draw_dashboard(screen, clock, pop, total_steps, mean_nodes, params, width, dashboard_size, font, temps_simule_ms):
    # Dessin du fond du bandeau
    pygame.draw.rect(screen, (20, 20, 20), (0, 0, width, dashboard_size-5)) # -5 pour laisser un petit gap
    pygame.draw.line(screen, (150, 150, 150), (0, dashboard_size-5), (width, dashboard_size-5), 2) # -5 pour laisser un petit gap

    # Calcul du temps écoulé (Temps réel depuis le lancement)
    secondes_ecoulees = int(temps_simule_ms) // 1000
    minutes = secondes_ecoulees // 60
    secondes = secondes_ecoulees % 60
    temps_txt = f"{minutes:02d}:{secondes:02d}" # Formatage 00:00

    # Informations à afficher
    # (MODE_FOOD : paramètre obsolète de l'ancienne physique nourriture — retiré)
    fps = int(clock.get_fps())
    txt_pop  = font.render(f"POPULATION: {pop}", True, (0, 255, 100) if pop > 0 else (255, 50, 50))
    txt_step = font.render(f"STEPS: {total_steps}", True, (200, 200, 200))
    txt_neurones = font.render(f"NOEUDS MOY: {mean_nodes:.1f}", True, (200, 150, 255))
    txt_fps  = font.render(f"FPS: {fps}", True, (255, 255, 0))
    txt_time = font.render(f"TIME: {temps_txt}", True, (255, 255, 255))

    # Positionnement sur le bandeau (TEST/MODE retirés)
    screen.blit(txt_step, (20, 15))
    screen.blit(txt_pop,  (250*1.4, 15))
    screen.blit(txt_neurones, (250*2.5, 15))
    screen.blit(txt_time, (250*3.5, 15))
    screen.blit(txt_fps,  (width-100, 15))

def show_graphics_off(screen, font, width, height, is_paused, dashboard_size):
    screen.fill((15, 15, 15)) # Fond très sombre
    txt_off = font.render(" GRAPHICS OFF (Intensive Computation) - Press 'G' to re-enable ", True, (150, 150, 150))
    screen.blit(txt_off, (width // 2 - txt_off.get_width() // 2, height // 2)) # On centre le texte
    if is_paused: graphics_pause(screen, font, dashboard_size)
    pygame.display.flip() 

def graphics_pause(screen, font, dashboard_size):
    # Texte jaune avec un fond gris foncé pour bien se détacher sans éblouir
    txt_pause = font.render(" SIMULATION EN PAUSE (Espace pour reprendre) ", True, (255, 200, 0), (40, 40, 40))
    screen.blit(txt_pause, (20, dashboard_size + 15))