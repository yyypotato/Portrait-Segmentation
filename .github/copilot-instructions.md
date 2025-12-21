# PortraitSeg AI Coding Instructions

## 1. Project Overview & Architecture
PortraitSeg is a desktop application for portrait segmentation and background replacement, built with **Python 3.11**, **PyQt6**, and **PyTorch**.

### Core Components
- **Entry Point**: `main.py` initializes the application, ensures directory structure (`output/`, `resources/weights`), and launches `MainWindow`.
- **GUI Layer** (`src/gui/`):
  - **MainWindow**: Uses `QStackedWidget` to manage navigation between pages (`MenuPage`, `SegPage`, `EditorPage`, `WorkbenchPage`).
  - **SegPage**: The core segmentation workflow (Upload -> Segment -> Composite -> Save).
  - **EditorPage**: Advanced image editing (Crop, Doodle, Mosaic, Filters) powered by `ImageEditorEngine`.
  - **Custom Widgets**: `CustomTitleBar` (frameless window), `ModernSlider`, `IconButton`.
- **Model Layer** (`src/models/`):
  - **Factory Pattern**: `ModelFactory` (`factory.py`) creates model instances based on string keys.
  - **Implementations**: `DeepLabModel` (`architectures/deeplab.py`) wraps `torchvision` models.
  - **Weight Management**: `TORCH_HOME` is explicitly set to `./resources/weights` in `deeplab.py` to keep weights local.
- **Utils**: `src/utils/image_processor.py` handles image transformations.

## 2. Critical Workflows & Commands

### Environment Setup
- **Python**: 3.11 recommended.
- **Dependencies**: `pip install -r requirements.txt`. Note: `torch` versions in `requirements.txt` are specific (e.g., `+cu118`).
- **Weights**: Automatically downloaded on first run to `resources/weights/hub/checkpoints`.

### Running the App
```bash
python main.py
```

### Development Tips
- **UI Changes**: When adding new pages, register them in `MainWindow`'s `QStackedWidget` and update `MenuPage` signals.
- **Model Integration**: To add a new model, implement `PortraitSegmentationModel` in `src/models/architectures/` and update `ModelFactory`.
- **Debugging**: Use `print()` or logging; output appears in the terminal.

## 3. Coding Conventions & Patterns

### GUI Development (PyQt6)
- **Styling**: Use inline stylesheets or `src/gui/styles.py` (if available). The app uses a dark theme (`#141824` background).
- **Threading**: Long-running tasks (like model inference) should ideally run in background threads (though currently may be synchronous in `SegPage` - check implementation).
- **Signals/Slots**: Use `pyqtSignal` for component communication (e.g., `go_back` signal in pages).
- **Images**: 
  - **Internal**: `numpy.ndarray` (OpenCV format, BGR/RGB).
  - **Display**: Convert to `QImage`/`QPixmap` for Qt widgets.
  - **Coordinate Systems**: Be careful when mapping mouse events on `QLabel`/`Canvas` back to the underlying numpy array.

### Image Processing
- **Engine**: `ImageEditorEngine` (`src/gui/editor/processor.py`) manages the edit state (original vs. preview image, parameters).
- **Performance**: Large images are resized for preview/inference to maintain responsiveness (`max_size` parameter).

### File Handling
- **Paths**: Use `os.path.join` or `pathlib`.
- **Resources**: Access resources relative to the project root.
- **Outputs**: Save results to `output/` by default.

## 4. Key Files
- `src/gui/main_window.py`: Main application shell and navigation logic.
- `src/gui/seg_page.py`: Segmentation logic and UI.
- `src/gui/editor/editor_page.py`: Image editor UI.
- `src/models/architectures/deeplab.py`: DeepLabV3+ implementation and weight handling.
- `src/models/factory.py`: Model instantiation logic.
