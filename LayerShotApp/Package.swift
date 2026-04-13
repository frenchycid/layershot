// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "LayerShotApp",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "LayerShotApp",
            path: "Sources/LayerShotApp",
            swiftSettings: [.unsafeFlags(["-parse-as-library"])]
        ),
        .testTarget(
            name: "LayerShotAppTests",
            dependencies: ["LayerShotApp"],
            path: "Tests"
        )
    ]
)
