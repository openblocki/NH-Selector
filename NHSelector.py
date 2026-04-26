from tkinter import filedialog

from Iota.Chunk import Chunk
from Iota.Region import Region
from Teto.Dim import Dim
from Zeta.MCAModifier import deleteRegions, delete_chunks
from Zeta.Tools import chunk_key, chunk_world_rect, is_dimension

def tile_color() -> str:
    return "default"


BG        = "#0b0e16"
PANEL_BG  = "#111827"
GRID_COL  = "#1c2333"
TEXT_PRI  = "#dde3f0"
TEXT_DIM  = "#4a5568"
ACCENT    = "#6c63ff"
SEL_RING  = "#f5c518"
BACK_COL  = "#1e293b"
ZOOM_LINE = "#2a3a5a"

def_color = {"normal": "#162030", "hover": "#1d3050",
                  "border": "#3d8ef0", "text": "#90c4ff", "badge": "#3d8ef0"}


REGION_TILE  = 96
CHUNK_TILE   = 96
PAD          = 50

import tkinter as tk

## Next time, ill just do it in c++ instead of doing whatever the hell all this is
class WorldVisualizer(tk.Tk):

    stopped = False

    def __init__(self):
        super().__init__()
        self.resizable(True, True)
        self.canvas = None
        self.not_a_dim_status = None
        self.dim_path: str = None
        self.get_dim_path()
        self.isDirty = False

        self._selection_start = None
        self._sel_rect_id = None

        if not is_dimension(self.dim_path):
            self.not_a_dim()
            return

        self.dim = Dim(self.dim_path)

        self.title(self.dim_path.split("/")[-2])
        self.configure(bg=BG)

        # view state
        self.view = "region"
        self.focused_rkey = None
        self.hovered = None
        self.selected_chunk = None
        self.clicked_chunks = []

        self.selected_region = None
        self.clicked_regions = []

        self._zoom = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._drag_start = None

        all_rx = [r.rx for r in self.dim.region_map.values()]
        all_ry = [r.ry for r in self.dim.region_map.values()]
        self.min_rx, self.max_rx = min(all_rx), max(all_rx)
        self.min_ry, self.max_ry = min(all_ry), max(all_ry)

        self._build_ui()
        self._reset_view()
        self._redraw()
        self.focus()

    def get_dim_path(self):
        main = tk.Frame(self, bg=BG)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
#

        canvas_frame = tk.Frame(main, bg=BG)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
#
        self.canvas = tk.Canvas(
            canvas_frame, bg=BG,
            highlightthickness=0, cursor="crosshair"
        )
        self.canvas.pack(fill=tk.BOTH, expand=False)
#
        self.not_a_dim_status = tk.StringVar(value="Select Dimension / region folder")
        tk.Label(canvas_frame, textvariable=self.not_a_dim_status,
                 font=("Courier New", 15), fg=TEXT_DIM, bg=BG,
                 anchor="w", padx=20, pady=80).pack(fill=tk.NONE)
        self.dim_path = tk.filedialog.askdirectory()
        self.canvas.delete(tk.ALL)
        canvas_frame.destroy()
        main.destroy()


    def not_a_dim(self):
        main = tk.Frame(self, bg=BG)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # canvas with scrollbars
        canvas_frame = tk.Frame(main, bg=BG)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            canvas_frame, bg=BG,
            highlightthickness=0, cursor="crosshair"
        )
        self.canvas.pack(fill=tk.BOTH, expand=False)

        self.not_a_dim_status = tk.StringVar(value="Selected Path is not a dimension")
        tk.Label(canvas_frame, textvariable=self.not_a_dim_status,
                 font=("Courier New", 15), fg=TEXT_DIM, bg=BG,
                 anchor="w", padx=20, pady=80).pack(fill=tk.NONE)


    # noinspection PyTypeChecker
    def _build_ui(self):

        #By God how is anybody supposed to read this
        self.toolbar = tk.Frame(self, bg=PANEL_BG, padx=12, pady=8)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.back_btn = tk.Button(
            self.toolbar, text=f"<- Back to {self.dim_path.split("/")[-1]}",
            font=("Courier New", 9, "bold"), fg=ACCENT, bg=BACK_COL,
            activeforeground="white", activebackground=ACCENT,
            bd=0, padx=10, pady=4, cursor="hand2",
            command=self._go_region_view, state=tk.DISABLED
        )
        self.back_btn.pack(side=tk.LEFT, padx=(0, 14))

        self.breadcrumb_var = tk.StringVar(value=f"{self.dim_path.split("/")[-2]} / {self.dim_path.split("/")[-1]}")
        tk.Label(self.toolbar, textvariable=self.breadcrumb_var,
                 font=("Courier New", 10, "bold"), fg=TEXT_PRI, bg=PANEL_BG
                 ).pack(side=tk.LEFT)

        tk.Label(self.toolbar,
                 text="Scroll to zoom - Middle-drag to pan - LClick to Select - RClick to inspect Region",
                 font=("Courier New", 8), fg=TEXT_DIM, bg=PANEL_BG
                 ).pack(side=tk.RIGHT)

        main = tk.Frame(self, bg=BG)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        canvas_frame = tk.Frame(main, bg=BG)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            canvas_frame, bg=BG,
            highlightthickness=0, cursor="crosshair"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value="Hover over a region…")
        tk.Label(canvas_frame, textvariable=self.status_var,
                 font=("Courier New", 9), fg=TEXT_DIM, bg=BG,
                 anchor="w", padx=12, pady=4).pack(fill=tk.X)

        panel = tk.Frame(main, bg=PANEL_BG, padx=16, pady=16, width=280)
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        panel.pack_propagate(False)

        tk.Label(panel, text="HOVER", font=("Courier New", 9, "bold"),
                    fg=ACCENT, bg=PANEL_BG, anchor="w").pack(fill=tk.X, pady=(0, 4))
        self.hover_info_var = tk.StringVar(value="—")
        tk.Label(panel, textvariable=self.hover_info_var,
                    font=("Courier New", 8), fg=TEXT_DIM, bg=PANEL_BG,
                    anchor="w", justify=tk.LEFT, wraplength=248
                    ).pack(fill=tk.X, pady=(0, 12))

        list_hdr = tk.Frame(panel, bg=PANEL_BG)
        list_hdr.pack(fill=tk.X, pady=(0, 6))
        tk.Label(list_hdr, text="CLICKED CHUNKS", font=("Courier New", 9, "bold"),
                 fg=ACCENT, bg=PANEL_BG).pack(side=tk.LEFT)
        tk.Button(list_hdr, text="Clear", font=("Courier New", 8),
                  fg="#d3ed28", bg=PANEL_BG, bd=0, cursor="hand2",
                  activeforeground="white", activebackground="#4a0a0a",
                  command=self._clear_clicks).pack(side=tk.RIGHT)
        tk.Button(list_hdr, text="DELETE", font=("Courier New", 8),
                   fg="#ff0000", bg="#e39400", bd=0, cursor="hand2",
                   activeforeground="white", activebackground="#4a0a0a",
                   command=self._delete_list).pack(side=tk.BOTTOM)

        list_wrap = tk.Frame(panel, bg=PANEL_BG)
        list_wrap.pack(fill=tk.BOTH, expand=True)
        sb = tk.Scrollbar(list_wrap, orient=tk.VERTICAL, bg=PANEL_BG, troughcolor=BG)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.click_listbox = tk.Listbox(
            list_wrap, bg=BG, fg=TEXT_PRI,
            font=("Courier New", 8), selectbackground=ACCENT,
            selectforeground="white", bd=0, highlightthickness=0,
            activestyle="none", yscrollcommand=sb.set
        )
        self.click_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self.click_listbox.yview)

        self.canvas.bind("<Configure>",    lambda e: self._redraw())
        self.canvas.bind("<Motion>",       self._on_mouse_move)
        self.canvas.bind("<Button-3>", self._on_right_click)

        self.canvas.bind("<Button-1>", self._on_selection_start)
        self.canvas.bind("<B1-Motion>", self._on_selection_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_selection_end)

        self.canvas.bind("<MouseWheel>",   self._on_scroll)          # Windows/Mac
        self.canvas.bind("<Button-4>",     self._on_scroll)          # Linux scroll up
        self.canvas.bind("<Button-5>",     self._on_scroll)          # Linux scroll down
        self.canvas.bind("<Button-2>",     self._on_pan_start)       # middle-drag
        self.canvas.bind("<B2-Motion>",    self._on_pan_move)

        self.update_idletasks()
        sw = self.winfo_screenwidth();  sh = self.winfo_screenheight()
        self.geometry(f"1280x780+{(sw-1280)//2}+{(sh-780)//2}")


    def _reset_view(self):
        self._zoom     = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0

    def _go_region_view(self):
        self.view          = "region"
        self.focused_rkey  = None
        self.selected_chunk = None
        self.hovered       = None
        self.back_btn.config(state=tk.DISABLED)
        self.breadcrumb_var.set(f"{self.dim_path.split("/")[-2]} / {self.dim_path.split("/")[-1]}")
        self._reset_view()
        self._redraw()
        self.status_var.set("Hover over a region…")
        self.hover_info_var.set("—")

    def _go_chunk_view(self, rkey: str):
        self.view          = "chunk"
        self.focused_rkey  = rkey
        self.selected_chunk = None
        self.hovered       = None
        region = self.dim.region_map[rkey]
        self.back_btn.config(state=tk.NORMAL)
        self.breadcrumb_var.set(f"{self.dim_path.split("/")[-2]} / {self.dim_path.split("/")[-1]} / r.{region.rx}.{region.ry}.mca")
        self._reset_view()
        self._redraw()
        self.status_var.set("Hover over a chunk…")
        self.hover_info_var.set("—")

    def _world_to_screen(self, wx, wy):
        return (wx * self._zoom + self._offset_x,
                wy * self._zoom + self._offset_y)

    def _screen_to_world(self, sx, sy):
        return ((sx - self._offset_x) / self._zoom,
                (sy - self._offset_y) / self._zoom)

    def _region_world_rect(self, region: Region):
        gx = region.rx - self.min_rx
        gy = region.ry - self.min_ry
        x1 = PAD + gx * REGION_TILE
        y1 = PAD + gy * REGION_TILE
        return x1, y1, x1 + REGION_TILE, y1 + REGION_TILE

    def _region_cols_rows(self):
        return (self.max_rx - self.min_rx + 1,
                self.max_ry - self.min_ry + 1)

    def _chunk_cols_rows(self, region: Region):
        all_x = [c.x for c in region.chunks]
        all_y = [c.z for c in region.chunks]
        return (max(all_x) - min(all_x) + 1,
                max(all_y) - min(all_y) + 1)

    def _region_at_screen(self, sx, sy):
        wx, wy = self._screen_to_world(sx, sy)
        for key, region in self.dim.region_map.items():
            x1, y1, x2, y2 = self._region_world_rect(region)
            if x1 <= wx <= x2 and y1 <= wy <= y2:
                return key
        return None

    def _chunk_at_screen(self, sx, sy):
        if not self.focused_rkey:
            return None
        region = self.dim.region_map[self.focused_rkey]
        wx, wy = self._screen_to_world(sx, sy)
        for chunk in region.chunks:
            x1, y1, x2, y2 = chunk_world_rect(chunk, region, PAD, CHUNK_TILE)
            if x1 <= wx <= x2 and y1 <= wy <= y2:
                return chunk_key(chunk)
        return None

    def _redraw(self):
        if self.stopped: return
        self.canvas.delete("all")
        if self.view == "region":
            self._draw_region_view()
        else:
            self._draw_chunk_view()

    def _s(self, wx, wy):
        return self._world_to_screen(wx, wy)

    def _draw_region_view(self):
        cols, rows = self._region_cols_rows()
        total_w = PAD * 2 + cols * REGION_TILE
        total_h = PAD * 2 + rows * REGION_TILE

        # background grid
        self._draw_bg_grid(total_w, total_h, REGION_TILE,
                           self.min_rx, self.min_ry, cols, rows)

        for key, region in self.dim.region_map.items():
            self._draw_region_tile(
                key, region,
                hover=(key == self.hovered),
                selected=(any(k == key
                              for k in self.clicked_regions))
            )

    def _draw_chunk_view(self):
        region = self.dim.region_map[self.focused_rkey]
        cols, rows = self._chunk_cols_rows(region)
        all_x = [c.x for c in region.chunks]
        all_y = [c.z for c in region.chunks]
        total_w = PAD * 2 + cols * CHUNK_TILE
        total_h = PAD * 2 + rows * CHUNK_TILE

        self._draw_bg_grid(total_w, total_h, CHUNK_TILE,
                           min(all_x), min(all_y), cols, rows)

        for chunk in region.chunks:
            ckey = chunk_key(chunk)
            self._draw_chunk_tile(
                chunk, region,
                hover=(ckey == self.hovered),
                selected=(any(k == ckey and r == self.focused_rkey
                              for r, k in self.clicked_chunks))
            )

    def _draw_bg_grid(self, tw, th, cell, ox, oy, cols, rows):
        for col in range(cols + 1):
            x = PAD + col * cell
            sx1, sy1 = self._s(x, PAD)
            sx2, sy2 = self._s(x, rows * cell)
            self.canvas.create_line(sx1, sy1, sx2, sy2, fill=GRID_COL)
        for row in range(rows + 1):
            y = PAD + row * cell
            sx1, sy1 = self._s(PAD, y)
            sx2, sy2 = self._s(PAD + cols * cell, y)
            self.canvas.create_line(sx1, sy1, sx2, sy2, fill=GRID_COL)

        fs = max(7, int(8 * self._zoom))
        for col in range(cols):
            lbl = ox + col
            cx = PAD + col * cell + cell // 2
            sx, sy = self._s(cx, PAD // 2)
            self.canvas.create_text(sx, sy, text=str(lbl),
                                    font=("Courier New", fs), fill=TEXT_DIM)
        for row in range(rows):
            lbl = oy + row
            cy = PAD + row * cell + cell // 2
            sx, sy = self._s(PAD // 2, cy)
            self.canvas.create_text(sx, sy, text=str(lbl),
                                    font=("Courier New", fs), fill=TEXT_DIM)

    def _draw_region_tile(self, key: str, region: Region,
                          hover: bool, selected: bool):

        x1w, y1w, x2w, y2w = self._region_world_rect(region)
        x1, y1 = self._s(x1w, y1w)
        x2, y2 = self._s(x2w, y2w)
        tag = f"R_{key}"
        self.canvas.delete(tag)

        fill  = def_color["hover"] if hover else def_color["normal"]
        bord  = SEL_RING if selected else def_color["border"]
        bw    = 3 if selected else 1

        self.canvas.create_rectangle(x1, y1, x2, y2,
                                     fill=fill, outline=bord, width=bw, tags=tag)

        z = self._zoom
        if z > 0.5:
            fs = max(7, int(9 * z))
            self.canvas.create_text((x1+x2)/2, y1 + 14*z,
                                    text=f"{region.rx},{region.ry}",
                                    font=("Courier New", fs, "bold"),
                                    fill=def_color["text"], tags=tag)
        if hover and z > 0.5:
            fs2 = max(6, int(8 * z))
            self.canvas.create_text((x1 + x2) / 2, y2 - 10 * z,
                                    text=f"{len(region.chunks)} chunks",
                                    font=("Courier New", fs2),
                                    fill=TEXT_DIM, tags=tag)
            self.canvas.create_text((x1+x2)/2, (y1+y2)/2,
                                    font=("Courier New", max(8, int(9*z)), "bold"),
                                    fill=def_color["text"], tags=tag)

    def _draw_chunk_tile(self, chunk: Chunk, region: Region,
                         hover: bool, selected: bool):
        x1w, y1w, x2w, y2w = chunk_world_rect(chunk, region)
        x1, y1 = self._s(x1w, y1w)
        x2, y2 = self._s(x2w, y2w)
        ckey = chunk_key(chunk)
        tag  = f"C_{ckey}"
        self.canvas.delete(tag)

        fill = def_color["hover"] if hover else def_color["normal"]
        bord = SEL_RING if selected else def_color["border"]
        bw   = 3 if selected else 1
        z    = self._zoom

        self.canvas.create_rectangle(x1, y1, x2, y2,
                                     fill=fill, outline=bord, width=bw, tags=tag)

        if z > 0.4:
            fs = max(7, int(8 * z))
            self.canvas.create_text((x1+x2)/2, y1 + 14*z,
                                    text=ckey,
                                    font=("Courier New", fs, "bold"),
                                    fill=def_color["text"], tags=tag)

        if selected:
            c = max(5, int(8 * z))

            #The Unholy block of Cheese, forgot how i wrote this, it just works
            for ax, ay, bx, by in [
                (x1, y1, x1+c, y1), (x1, y1, x1, y1+c),
                (x2, y1, x2-c, y1), (x2, y1, x2, y1+c),
                (x1, y2, x1+c, y2), (x1, y2, x1, y2-c),
                (x2, y2, x2-c, y2), (x2, y2, x2, y2-c),
            ]:
                self.canvas.create_line(ax, ay, bx, by,
                                        fill=SEL_RING, width=1, tags=tag)

    def _on_mouse_move(self, event):
        if self.stopped: return
        sx, sy = event.x, event.y
        if self.view == "region":
            key = self._region_at_screen(sx, sy)
            if key != self.hovered:
                self.hovered = key
                self._redraw()
            if key:
                r = self.dim.region_map[key]
                self.status_var.set(
                    f"Region ({r.rx},{r.ry})  ·  {len(r.chunks)} chunks"
                )
                self.hover_info_var.set(
                    f"Chunks:   {len(r.chunks)}\n"
                    f"Chunk Area: [{r.rx*16},{r.ry*16}] - [{r.rx*16+15}, {r.ry*16+15}]\n"
                    f"Block Area: [{r.rx*512},{r.ry*512}] - [{r.rx*512+511}, {r.ry*512+511}]\n"
                )
            else:
                self.status_var.set("Hover over a region…")
                self.hover_info_var.set("—")

        else:
            key = self._chunk_at_screen(sx, sy)
            if key != self.hovered:
                self.hovered = key
                self._redraw()
            if key:
                region = self.dim.region_map[self.focused_rkey]
                chunk  = region._chunk_map[key]
                self.status_var.set(f"Chunk ({chunk.x},{chunk.z})")
                self.hover_info_var.set(
                    f"Chunk ({chunk.x},{chunk.z})\n"
                    f"Block Area: [{chunk.x * 16},{chunk.z * 16}] - [{chunk.x * 16 + 15}, {chunk.z * 16 + 15}]"
                )
            else:
                self.status_var.set("Hover over a chunk…")
                self.hover_info_var.set("—")

    def _on_right_click(self, event):
        if self.stopped: return
        sx, sy = event.x, event.y
        if self.view == "region":
            key = self._region_at_screen(sx, sy)
            if key:
                self._go_chunk_view(key)

    def _on_selection_start(self, event):
        self._selection_start = (event.x, event.y)
        if self._sel_rect_id:
            self.canvas.delete(self._sel_rect_id)
        self._sel_rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline=ACCENT, dash=(4, 4), width=2
        )

    def _on_selection_drag(self, event):
        if not self._selection_start: return
        x1, y1 = self._selection_start
        self.canvas.coords(self._sel_rect_id, x1, y1, event.x, event.y)

    def _on_selection_end(self, event):
        if not self._selection_start: return

        x1, y1 = self._selection_start
        x2, y2 = event.x, event.y

        sel_x1, sel_x2 = sorted([x1, x2])
        sel_y1, sel_y2 = sorted([y1, y2])

        if (sel_x2 - sel_x1) < 3 and (sel_y2 - sel_y1) < 3:
            self._on_click(event)
        else:
            self._process_box_selection(sel_x1, sel_y1, sel_x2, sel_y2)

        if self._sel_rect_id:
            self.canvas.delete(self._sel_rect_id)
            self._sel_rect_id = None
        self._selection_start = None
        self._rebuild_listbox()
        self._redraw()

    def _rebuild_listbox(self):
        self.click_listbox.delete(0, tk.END)
        for chunk in self.clicked_chunks:
            self.click_listbox.insert(tk.END, f"C: {chunk[1]}")
        for region in self.clicked_regions:
            self.click_listbox.insert(tk.END, f"R: {region}")


    def _process_box_selection(self, sx1, sy1, sx2, sy2):
        wx1, wy1 = self._screen_to_world(sx1, sy1)
        wx2, wy2 = self._screen_to_world(sx2, sy2)

        if self.view == "region":
            for key, region in self.dim.region_map.items():
                rx1, ry1, rx2, ry2 = self._region_world_rect(region)
                if not (rx2 < wx1 or rx1 > wx2 or ry2 < wy1 or ry1 > wy2):
                    if key not in self.clicked_regions:
                        self.clicked_regions.append(key)
                        self.click_listbox.insert(tk.END, f"  R: {key}")
                    else:
                        self.clicked_regions.remove(key)
        else:
            region = self.dim.region_map[self.focused_rkey]
            for chunk in region.chunks:
                ckey = chunk_key(chunk)
                cx1, cy1, cx2, cy2 = chunk_world_rect(chunk, region, PAD, CHUNK_TILE)
                if not (cx2 < wx1 or cx1 > wx2 or cy2 < wy1 or cy1 > wy2):
                    entry = (self.focused_rkey, ckey)
                    if entry not in self.clicked_chunks:
                        self.clicked_chunks.append(entry)
                        self.click_listbox.insert(tk.END, f"  C: {ckey} ({region.rx},{region.ry})")
                    else:
                        self.clicked_chunks.remove(entry)

        self.click_listbox.yview_moveto(1)

    def _on_click(self, event):
        if self.stopped: return
        sx, sy = event.x, event.y
        if self.view == "region":
            key = self._region_at_screen(sx, sy)
            if key:
                self.selected_region = key
                region = self.dim.region_map[key]

                if key not in self.clicked_regions:
                    self.clicked_regions.append(key)
                    self.click_listbox.insert(
                        tk.END,
                        f"  {len(self.clicked_chunks):02d}. Region({region.rx},{region.ry})"
                    )
                else:
                    self.clicked_regions.remove(key)

        else:
            key = self._chunk_at_screen(sx, sy)
            if key:
                self.selected_chunk = key
                region = self.dim.region_map[self.focused_rkey]
                chunk = region._chunk_map[key]
                entry  = (self.focused_rkey, key)
                if entry not in self.clicked_chunks:
                    self.clicked_chunks.append(entry)
                    self.click_listbox.insert(
                        tk.END,
                        f"  {len(self.clicked_chunks):02d}. Chunk {chunk.x},{chunk.z} R({region.rx},{region.ry})")
                else:
                    self.clicked_chunks.remove(entry)

        self.click_listbox.yview_moveto(1)

    def _on_scroll(self, event):
        if self.stopped: return
        if event.num == 4:
            delta = 1
        elif event.num == 5:
            delta = -1
        else:
            delta = event.delta

        factor = 1.12 if delta > 0 else 1 / 1.12
        sx, sy = event.x, event.y
        self._offset_x = sx - (sx - self._offset_x) * factor
        self._offset_y = sy - (sy - self._offset_y) * factor
        self._zoom = max(0.15, min(self._zoom * factor, 6.0))
        self._redraw()

    def _on_pan_start(self, event):
        self._drag_start = (event.x, event.y)

    def _on_pan_move(self, event):
        if self._drag_start:
            dx = event.x - self._drag_start[0]
            dy = event.y - self._drag_start[1]
            self._offset_x += dx
            self._offset_y += dy
            self._drag_start = (event.x, event.y)
            self._redraw()

    def _clear_clicks(self):
        self.clicked_chunks = []
        self.clicked_regions = []
        self.selected_chunk = None
        self.selected_region = None
        self.click_listbox.delete(0, tk.END)
        self._redraw()

    def _delete_list(self):
        self.stopped = True
        regions = {}

        for region, chunk in self.clicked_chunks:
            if region in regions:
                regions[region].append(chunk)
            else:
                regions[region] = []
                regions[region].append(chunk)

        for key, value in regions.items():
            x, z = key.split(",")
            chunks = []
            for chunk in value:
                cx, cz = chunk.split(",")
                chunks.append(Chunk(cx, cz))

            delete_chunks(self.dim_path, x, z, chunks)

        deleteRegions(self.dim_path, self.clicked_regions)

        self.clicked_chunks = []
        self.clicked_regions = []
        self.selected_chunk = None
        self.selected_region = None
        self.click_listbox.delete(0, tk.END)
        self.dim = None
        self.dim = Dim(self.dim_path)
        self.stopped = False
        self._redraw()
        return

if __name__ == "__main__":
    app = WorldVisualizer()
    app.mainloop()