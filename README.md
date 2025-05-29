# Bangladesh Railway Ticket Booking System

A well-architected Python application for booking train tickets on the Bangladesh Railway e-ticket system. This system uses clean architecture principles with clear separation of concerns between business logic and infrastructure.

## Features

- 🚂 Automated train ticket booking
- 🔄 Automatic retry mechanism for failed bookings
- 🎯 Smart seat selection
- 📱 Multiple passenger booking support
- 🔒 Authentication handling
- 💾 Intelligent caching system
- 📊 Comprehensive logging
- ⚡ Async/await for better performance

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/joynahiid/fast-ticket.git
cd fast-ticket
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your booking details in `config.py`:
```python
config = BookingConfig(
    mobile_number="your_mobile_number",
    password="your_password",
    seat_class="SNIGDHA",
    passenger_names=["PASSENGER_NAME_1", "PASSENGER_NAME_2"],
    passenger_genders=["male", "female"],
    passenger_types=["Adult", "Adult"]
)
```

## Usage

### Basic Usage

```bash
# Book the first available trip
python main.py

# Book a specific trip number
python main.py --trip 2

# Refresh cache and book
python main.py --refresh

# Override journey details via CLI
python main.py --from-city "Dhaka" --to-city "Chittagong" --journey-date "28-May-2025"
```

### CLI Options

- `--trip, -t`: Trip number to book (default: 1)
- `--refresh, -r`: Refresh cache and fetch fresh data
- `--from-city, -f`: Source city (overrides config)
- `--to-city, -T`: Destination city (overrides config)  
- `--journey-date, -d`: Journey date in DD-MMM-YYYY format (overrides config)

## Architecture

The application follows clean architecture principles with three main layers:

1. **Application Layer**: Orchestrates the business logic and coordinates between different services
2. **Business Layer**: Contains the core business logic and domain rules
3. **Infrastructure Layer**: Handles external systems and implementations

## Contributing

I'm actively looking for contributors! Please contact me at nahidhasan282@gmail.com or open an issue.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Bangladesh Railway for providing the e-ticket system
- All contributors who have helped improve this project

## Support

If you encounter any issues or have questions, please:
1. Check the [existing issues](https://github.com/joynahiid/fast-ticket/issues)
2. Create a new issue if your problem hasn't been reported
