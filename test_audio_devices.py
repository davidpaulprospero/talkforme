"""Test script to detect audio activity on all input devices."""

import pyaudio
import struct
import math
import time
import sys

def get_rms(audio_data):
    """Calculate RMS (Root Mean Square) of audio data."""
    try:
        count = len(audio_data) // 2
        format_str = f"{count}h"
        shorts = struct.unpack(format_str, audio_data)
        sum_squares = sum(s ** 2 for s in shorts)
        rms = math.sqrt(sum_squares / count)
        return rms
    except:
        return 0

def test_all_devices():
    """Test all audio input devices for activity."""
    p = pyaudio.PyAudio()

    # Get all input devices
    input_devices = []
    for i in range(p.get_device_count()):
        try:
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append({
                    'index': i,
                    'name': device_info['name'],
                    'sample_rate': int(device_info['defaultSampleRate'])
                })
        except:
            continue

    print(f"Found {len(input_devices)} input devices")
    print("Starting audio detection... (Press Ctrl+C to stop)")
    print("=" * 80)
    print()

    # Open streams for all devices
    streams = []
    for device in input_devices:
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,  # Use consistent sample rate
                input=True,
                input_device_index=device['index'],
                frames_per_buffer=1024,
                start=False
            )
            stream.start_stream()
            streams.append({
                'stream': stream,
                'device': device
            })
        except Exception as e:
            print(f"[{device['index']}] {device['name']}: ERROR - {str(e)}")
            continue

    print(f"Successfully opened {len(streams)} streams")
    print()

    try:
        while True:
            # Clear screen (Windows)
            print("\033[H\033[J", end="")
            print("AUDIO DEVICE MONITOR - Active devices shown with level")
            print("=" * 80)
            print()

            active_devices = []

            for stream_info in streams:
                stream = stream_info['stream']
                device = stream_info['device']

                try:
                    # Read audio data
                    if stream.is_active() and stream.get_read_available() > 0:
                        audio_data = stream.read(1024, exception_on_overflow=False)
                        rms = get_rms(audio_data)

                        # Threshold for "active" audio
                        if rms > 100:  # Adjust this threshold as needed
                            level_bars = int(min(rms / 100, 50))
                            bar = "#" * level_bars
                            active_devices.append({
                                'index': device['index'],
                                'name': device['name'],
                                'rms': rms,
                                'bar': bar
                            })
                except Exception as e:
                    pass

            if active_devices:
                # Sort by RMS level (loudest first)
                active_devices.sort(key=lambda x: x['rms'], reverse=True)

                for dev in active_devices:
                    print(f"[{dev['index']:3d}] {dev['name'][:50]:50s} | {dev['bar']} ({int(dev['rms'])})")
            else:
                print("No active audio detected on any device...")
                print()
                print("Make sure audio is playing and devices are properly configured.")

            print()
            print("=" * 80)
            print("Press Ctrl+C to stop")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        # Clean up
        for stream_info in streams:
            try:
                stream_info['stream'].stop_stream()
                stream_info['stream'].close()
            except:
                pass
        p.terminate()

if __name__ == "__main__":
    test_all_devices()
