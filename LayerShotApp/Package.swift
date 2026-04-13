// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "LayerShotApp",
    platforms: [.macOS(.v14)],
    targets: [
        .target(
            name: "LayerShotApp",
            path: "Sources/LayerShotApp"
        ),
        .executableTarget(
            name: "LayerShotAppExecutable",
            dependencies: ["LayerShotApp"],
            path: "Sources/LayerShotAppExecutable"
        ),
        .executableTarget(
            name: "LayerShotAppTests",
            dependencies: ["LayerShotApp"],
            path: "Tests/LayerShotAppTests"
        )
    ]
)
