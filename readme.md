# SSVEP BCI System

---
## GUI Page
- Person INfO
- EEG device(LSL)
- Data Collect
- Analysis
- Realtime

## Data Format
```
Data_/
└── ID_i/ 
    ├── +.npy          
    ├── up.npy
    ├── down.npy
    ├── left.npy
    ├── right.npy
    ├── events.csv
    └── person_info.json
```

## API 
- Psychopy: https://www.psychopy.org/api/index.html#api
- CCA: https://scikit-learn.org/stable/modules/generated/sklearn.cross_decomposition.CCA.html
- LSL: https://docs.pypi.org/


## Environment
```
Python = 3.10
    tkinter: GUI
    pylsl: LSL Scan|Connect|Get data 
    psychopy: Stimuli
    sklearn: CCA
    numpy: Data format
    scipy: Band filter
    screeninfo: get screen info
    multiprocessing: Manager process
    websockets: Realtime game
    cv2: Image process
```