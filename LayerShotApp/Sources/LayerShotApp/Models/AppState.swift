// LayerShotApp/Sources/LayerShotApp/Models/AppState.swift
import SwiftUI
import Observation

@Observable
class AppState {
    var pythonPath: String = "/usr/bin/python3"
    var projectPath: String = NSHomeDirectory() + "/projects/layershot"
}
