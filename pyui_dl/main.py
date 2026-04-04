import os
import sys

import pygame

from pyui_dl.editor.selector import Selector
from pyui_dl.logic.editor import LogicEditor
from pyui_dl.logic.models import LogicData
from pyui_dl.logic.serializer import LogicSerializer
from pyui_dl.ui.widget import Widget
from pyui_dl.utils.serializer import Serializer


def main():
    pygame.init()

    file_name = "sample_ui"
    screen_w = 450
    screen_h = 700

    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            screen_w = int(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid width '{sys.argv[2]}'. Using default {screen_w}.")
    if len(sys.argv) > 3:
        try:
            screen_h = int(sys.argv[3])
        except ValueError:
            print(f"Warning: Invalid height '{sys.argv[3]}'. Using default {screen_h}.")

    if not file_name.endswith(".json"):
        file_name += ".json"
    ui_path = os.path.join("data", file_name)
    logic_path = LogicSerializer.logic_path_from_ui_path(ui_path)

    if not os.path.exists("data"):
        os.makedirs("data")

    screen = pygame.display.set_mode((screen_w, screen_h), pygame.RESIZABLE)
    pygame.display.set_caption(
        f"UI Ultra Editor + Logic - {file_name} ({screen_w}x{screen_h})"
    )

    Widget.debug_mode = True
    try:
        ui_root = Serializer.load_file(ui_path)
        print(f"Loaded UI: {ui_path}")
    except FileNotFoundError:
        from pyui_dl.ui.layout import VBox

        print(f"Creating new layout: {file_name}")
        ui_root = VBox(name="Root")

    try:
        logic = LogicSerializer.load_file(logic_path)
        print(f"Loaded Logic: {logic_path}")
    except FileNotFoundError:
        logic = LogicData()
        print(f"New logic file: {logic_path}")

    ui_root.update_layout(0, 0, screen_w, screen_h)

    selector = Selector()
    logic_editor = LogicEditor(logic)
    clock = pygame.time.Clock()

    while True:
        mouse_pos = pygame.mouse.get_pos()

        if not logic_editor.enabled:
            if selector.update(mouse_pos):
                ui_root.update_layout(0, 0, screen.get_width(), screen.get_height())

        logic_editor.set_widget(selector.selected_widget)

        events = pygame.event.get()
        cmd_done = False

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if not logic_editor.enabled:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    selector.start_select(ui_root, mouse_pos)
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    selector.stop_drag()

            if event.type == pygame.KEYDOWN:
                ctrl = bool(pygame.key.get_mods() & pygame.KMOD_CTRL)

                if ctrl and event.key == pygame.K_s:
                    Serializer.save_file(ui_root, ui_path)
                    LogicSerializer.save_file(logic, logic_path)
                    print(f"Saved UI:    {ui_path}")
                    print(f"Saved Logic: {logic_path}")
                    cmd_done = True

                elif ctrl and event.key == pygame.K_e:
                    logic_editor.toggle()
                    mode = "LOGIC" if logic_editor.enabled else "DESIGN"
                    print(f"Mode: {mode}")
                    cmd_done = True

                else:
                    if logic_editor.enabled:
                        logic_editor.handle_keydown(event)
                        # SUB_INPUT中はTEXTINPUTも通す必要があるためcmd_doneを立てない
                        if not logic_editor.is_inputting():
                            cmd_done = True
                    else:
                        if selector.handle_input(event, ui_root):
                            ui_root.update_layout(
                                0, 0, screen.get_width(), screen.get_height()
                            )
                            cmd_done = True

            if event.type == pygame.VIDEORESIZE:
                ui_root.update_layout(0, 0, event.w, event.h)

        if not cmd_done:
            for event in events:
                if event.type == pygame.TEXTINPUT:
                    if logic_editor.enabled:
                        logic_editor.handle_text_input(event.text)
                    else:
                        selector.handle_text_input(event.text)

        screen.fill((40, 40, 40))
        ui_root.draw(screen)
        selector.draw(screen)
        logic_editor.draw(screen)
        _draw_mode_indicator(screen, logic_editor.enabled)

        pygame.display.flip()
        clock.tick(60)


def _draw_mode_indicator(screen, logic_mode: bool):
    font = pygame.font.SysFont(None, 20)
    w = screen.get_width()
    label = "[ LOGIC MODE ]" if logic_mode else "[ DESIGN MODE ]"
    col = (255, 140, 40) if logic_mode else (80, 220, 160)
    surf = font.render(label, True, col)
    bg = pygame.Surface((surf.get_width() + 16, surf.get_height() + 8), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 160))
    screen.blit(bg, (w - bg.get_width() - 8, 8))
    screen.blit(surf, (w - surf.get_width() - 16, 12))


if __name__ == "__main__":
    main()
