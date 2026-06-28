"""
Wangz Camera Prompt Studio Node for ComfyUI
카메라 앵글 + 렌즈 종류 + 심도 + 필터 + 기본 프롬프트를 통합한 노드

Created by Wangz
"""

# ─────────────────────────────────────────────
#  드롭다운 옵션 정의
# ─────────────────────────────────────────────

HORIZONTAL_LABELS = ["front", "front-right quarter", "right side", "rear-right quarter",
                     "rear", "rear-left quarter", "left side", "front-left quarter"]

VERTICAL_LABELS = ["extreme low-angle", "low-angle", "eye-level", "slightly high-angle",
                   "high-angle", "bird's eye view"]

DISTANCE_LABELS = ["extreme close-up", "close-up", "medium close-up", "medium shot",
                   "medium full shot", "full shot", "wide shot", "extreme wide shot"]

LENS_TYPE_OPTIONS = [
    "none",
    "85mm portrait lens",
    "50mm standard lens",
    "35mm cinematic lens",
    "28mm wide-angle lens",
    "135mm telephoto lens",
    "Anamorphic lens",
    "Vintage 1980s camera lens",
    "Macro lens",
    "Fisheye lens",
    "Panavision 70mm lens",
]

DOF_OPTIONS = [
    "none",
    "shallow depth of field, bokeh background",
    "extremely shallow depth of field, heavy bokeh",
    "deep sharp focus, everything in focus",
    "out of focus, dreamy blur",
    "rack focus, subject sharp background soft",
    "tilt-shift miniature effect",
]

FILM_FILTER_OPTIONS = [
    "none",
    "mist diffusion filter, soft glow",
    "35mm film grain, analog texture",
    "light leak effect, warm color bleed",
    "cross-process film effect, shifted colors",
    "infrared film effect",
    "vintage Kodachrome color grade",
    "heavy vignette, dark edges",
    "anamorphic lens flare, horizontal streaks",
    "double exposure, layered transparency",
]

MOOD_PRESET_OPTIONS = [
    "none",
    "city pop retro, 1980s Japan aesthetic, neon reflections, warm summer night",
    "ethereal dreamy, soft pastel haze, otherworldly glow",
    "dark moody cinematic, high contrast, dramatic shadows",
    "golden hour, warm sunlight, glowing rim light",
    "neon noir, rain-soaked streets, cyberpunk atmosphere",
    "lo-fi aesthetic, melancholic, muted tones",
    "editorial fashion, clean minimal, studio lighting",
    "horror atmospheric, cold tones, eerie fog",
]


# ─────────────────────────────────────────────
#  노드 클래스
# ─────────────────────────────────────────────

class CameraPromptStudio:
    """
    카메라 앵글·렌즈·심도·필터·무드를 통합 관리하는 프롬프트 스튜디오 노드.
    출력: 완성된 텍스트 프롬프트 (str)
    """

    CATEGORY = "Wangz/camera"
    FUNCTION = "generate_prompt"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # ── 카메라 앵글 ──────────────────────────────
                "horizontal_angle": (HORIZONTAL_LABELS, {"default": "front-right quarter"}),
                "vertical_angle":   (VERTICAL_LABELS,   {"default": "slightly high-angle"}),
                "shot_distance":    (DISTANCE_LABELS,   {"default": "close-up"}),

                # ── 렌즈 / 심도 / 필터 ──────────────────────
                "lens_type":    (LENS_TYPE_OPTIONS,    {"default": "85mm portrait lens"}),
                "depth_of_field": (DOF_OPTIONS,        {"default": "shallow depth of field, bokeh background"}),
                "film_filter":  (FILM_FILTER_OPTIONS,  {"default": "none"}),

                # ── 무드 프리셋 ──────────────────────────────
                "mood_preset":  (MOOD_PRESET_OPTIONS,  {"default": "none"}),

                # ── 기본 프롬프트 (자유 입력) ─────────────────
                "base_prompt": ("STRING", {
                    "multiline": True,
                    "default": (
                        "Japanese Gothic-style ribbon-decorated maid girl"
                    ),
                }),

                # ── 후미 파라미터 (Midjourney / Flux 등) ────
                "tail_params": ("STRING", {
                    "multiline": False,
                    "default": "--ar 16:9 --v 6.0",
                }),

                # ── 출력 포맷 옵션 ───────────────────────────
                "separator": (["comma", "newline", "comma+newline"], {"default": "comma"}),
                "include_angle_prefix": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                # 외부 노드(Qwen Multiangle 등)에서 오는 앵글 텍스트를 덮어쓰기로 사용
                "external_angle_prompt": ("STRING", {"forceInput": True}),
            },
        }

    # ── 메인 함수 ────────────────────────────────────────────────────────────

    def generate_prompt(
        self,
        horizontal_angle,
        vertical_angle,
        shot_distance,
        lens_type,
        depth_of_field,
        film_filter,
        mood_preset,
        base_prompt,
        tail_params,
        separator,
        include_angle_prefix,
        external_angle_prompt=None,
    ):
        sep = {"comma": ", ", "newline": "\n", "comma+newline": ",\n"}[separator]

        # 1) 카메라 앵글 블록
        if external_angle_prompt and external_angle_prompt.strip():
            angle_block = external_angle_prompt.strip()
        else:
            parts = [horizontal_angle, vertical_angle, shot_distance]
            angle_block = " ".join(p for p in parts if p)
            if include_angle_prefix:
                angle_block = f"<sks> {angle_block}"

        # 2) 카메라 스펙 블록 (렌즈 + 심도 + 필터)
        camera_spec_parts = []
        if lens_type and lens_type != "none":
            camera_spec_parts.append(lens_type)
        if depth_of_field and depth_of_field != "none":
            camera_spec_parts.append(depth_of_field)
        if film_filter and film_filter != "none":
            camera_spec_parts.append(film_filter)
        camera_spec_block = sep.join(camera_spec_parts) if camera_spec_parts else ""

        # 3) 무드 프리셋
        mood_block = mood_preset if mood_preset and mood_preset != "none" else ""

        # 4) 기본 프롬프트
        base_block = base_prompt.strip()

        # 5) 최종 조합: 앵글 → 카메라 스펙 → 기본 프롬프트 → 무드 → 파라미터
        blocks = [angle_block, camera_spec_block, base_block, mood_block]
        body = sep.join(b for b in blocks if b)

        # tail_params는 항상 맨 뒤, 공백으로 구분
        if tail_params and tail_params.strip():
            final_prompt = body + " " + tail_params.strip()
        else:
            final_prompt = body

        return (final_prompt,)


# ─────────────────────────────────────────────
#  ComfyUI 등록
# ─────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "WangzCameraPromptStudio": CameraPromptStudio,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WangzCameraPromptStudio": "📷 Wangz Camera Prompt Studio",
}
